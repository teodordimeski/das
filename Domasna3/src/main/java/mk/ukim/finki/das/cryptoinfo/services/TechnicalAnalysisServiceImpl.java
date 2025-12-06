package mk.ukim.finki.das.cryptoinfo.services;

import mk.ukim.finki.das.cryptoinfo.dto.MovingAverageIndicatorDTO;
import mk.ukim.finki.das.cryptoinfo.dto.OscillatorIndicatorDTO;
import mk.ukim.finki.das.cryptoinfo.dto.TechnicalAnalysisResponseDTO;
import mk.ukim.finki.das.cryptoinfo.model.CryptoSymbol;
import mk.ukim.finki.das.cryptoinfo.repository.CryptoSymbolInterface;
import org.springframework.stereotype.Service;
import org.ta4j.core.*;
import org.ta4j.core.indicators.*;
import org.ta4j.core.indicators.adx.ADXIndicator;
import org.ta4j.core.indicators.statistics.StandardDeviationIndicator;
import org.ta4j.core.indicators.StochasticOscillatorKIndicator;
import org.ta4j.core.indicators.helpers.ClosePriceIndicator;
import org.ta4j.core.indicators.helpers.VolumeIndicator;

import java.time.LocalDate;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.ArrayList;
import java.util.List;

@Service
public class TechnicalAnalysisServiceImpl implements TechnicalAnalysisService {

    private final CryptoSymbolInterface repository;

    public TechnicalAnalysisServiceImpl(CryptoSymbolInterface repository) {
        this.repository = repository;
    }

    @Override
    public TechnicalAnalysisResponseDTO getTechnicalAnalysis(String symbol, String timeframe) {
        // Fetch all historical data for the symbol
        List<CryptoSymbol> allData = repository.findBySymbolIgnoreCaseOrderByDateAsc(symbol);
        
        if (allData.isEmpty()) {
            throw new IllegalArgumentException("No data found for symbol: " + symbol);
        }

        // Aggregate data by timeframe if needed
        List<CryptoSymbol> aggregatedData = aggregateByTimeframe(allData, timeframe);

        // Convert to TA4J BarSeries
        BarSeries series = convertToBarSeries(aggregatedData);

        if (series.getBarCount() < 50) {
            // Need at least 50 bars for most indicators
            throw new IllegalArgumentException("Insufficient data points for technical analysis. Need at least 50 bars.");
        }

        // Calculate oscillators
        List<OscillatorIndicatorDTO> oscillators = calculateOscillators(series);

        // Calculate moving averages
        List<MovingAverageIndicatorDTO> movingAverages = calculateMovingAverages(series);

        // Calculate summaries
        TechnicalAnalysisResponseDTO.OscillatorSummary oscillatorSummary = calculateOscillatorSummary(oscillators);
        TechnicalAnalysisResponseDTO.MovingAverageSummary movingAverageSummary = calculateMovingAverageSummary(movingAverages);

        return new TechnicalAnalysisResponseDTO(
                symbol,
                timeframe,
                oscillatorSummary,
                movingAverageSummary,
                oscillators,
                movingAverages
        );
    }

    @Override
    public List<CryptoSymbol> aggregateByTimeframe(List<CryptoSymbol> data, String timeframe) {
        if ("DAILY".equalsIgnoreCase(timeframe)) {
            return data;
        }

        List<CryptoSymbol> aggregated = new ArrayList<>();
        CryptoSymbol currentAggregate = null;
        LocalDate currentPeriod = null;

        for (CryptoSymbol entry : data) {
            LocalDate periodStart = getPeriodStart(entry.getDate(), timeframe);

            if (currentPeriod == null || !currentPeriod.equals(periodStart)) {
                // Save previous aggregate
                if (currentAggregate != null) {
                    aggregated.add(currentAggregate);
                }

                // Start new aggregate
                currentPeriod = periodStart;
                currentAggregate = new CryptoSymbol();
                currentAggregate.setDate(periodStart);
                currentAggregate.setSymbol(entry.getSymbol());
                currentAggregate.setOpen(entry.getOpen());
                currentAggregate.setHigh(entry.getHigh());
                currentAggregate.setLow(entry.getLow());
                currentAggregate.setClose(entry.getClose());
                currentAggregate.setVolume(entry.getVolume() != null ? entry.getVolume() : 0.0);
                currentAggregate.setBaseAsset(entry.getBaseAsset());
                currentAggregate.setQuoteAsset(entry.getQuoteAsset());
                currentAggregate.setSymbolUsed(entry.getSymbolUsed());
            } else {
                // Update aggregate with this period's data
                if (currentAggregate != null) {
                    currentAggregate.setHigh(Math.max(currentAggregate.getHigh(), entry.getHigh()));
                    currentAggregate.setLow(Math.min(currentAggregate.getLow(), entry.getLow()));
                    currentAggregate.setClose(entry.getClose());
                    currentAggregate.setVolume((currentAggregate.getVolume() != null ? currentAggregate.getVolume() : 0.0) + 
                                             (entry.getVolume() != null ? entry.getVolume() : 0.0));
                }
            }
        }

        // Add last aggregate
        if (currentAggregate != null) {
            aggregated.add(currentAggregate);
        }

        return aggregated;
    }

    private LocalDate getPeriodStart(LocalDate date, String timeframe) {
        if ("WEEKLY".equalsIgnoreCase(timeframe)) {
            // Start of week (Monday)
            return date.minusDays(date.getDayOfWeek().getValue() - 1);
        } else if ("MONTHLY".equalsIgnoreCase(timeframe)) {
            // Start of month
            return date.withDayOfMonth(1);
        }
        return date;
    }

    private BarSeries convertToBarSeries(List<CryptoSymbol> data) {
        BarSeries series = new BaseBarSeriesBuilder().withName("CryptoData").build();

        for (CryptoSymbol symbol : data) {
            if (symbol.getOpen() != null && symbol.getHigh() != null && 
                symbol.getLow() != null && symbol.getClose() != null &&
                symbol.getDate() != null) {
                
                try {
                    ZonedDateTime barTime = symbol.getDate().atStartOfDay(ZoneId.systemDefault());
                    double volume = symbol.getVolume() != null && symbol.getVolume() > 0 ? symbol.getVolume() : 0;
                    
                    series.addBar(barTime, 
                        series.numOf(symbol.getOpen()),
                        series.numOf(symbol.getHigh()),
                        series.numOf(symbol.getLow()),
                        series.numOf(symbol.getClose()),
                        series.numOf(volume)
                    );
                } catch (Exception e) {
                    // Skip invalid bars
                    continue;
                }
            }
        }

        return series;
    }

    private List<OscillatorIndicatorDTO> calculateOscillators(BarSeries series) {
        List<OscillatorIndicatorDTO> oscillators = new ArrayList<>();
        ClosePriceIndicator closePrice = new ClosePriceIndicator(series);

        // RSI (14)
        int rsiPeriod = 14;
        RSIIndicator rsi = new RSIIndicator(closePrice, rsiPeriod);
        if (series.getBarCount() > rsiPeriod) {
            double rsiValue = rsi.getValue(series.getEndIndex()).doubleValue();
            String rsiSignal = getRSISignal(rsiValue);
            oscillators.add(new OscillatorIndicatorDTO(
                "RSI",
                round(rsiValue, 2),
                rsiSignal,
                String.format("Relative Strength Index (%d)", rsiPeriod)
            ));
        }

        // MACD (12, 26, 9)
        MACDIndicator macd = new MACDIndicator(closePrice, 12, 26);
        if (series.getBarCount() > 26) {
            double macdValue = macd.getValue(series.getEndIndex()).doubleValue();
            String macdSignal = macdValue > 0 ? "BUY" : "SELL";
            oscillators.add(new OscillatorIndicatorDTO(
                "MACD",
                round(macdValue, 2),
                macdSignal,
                "MACD Level (12, 26)"
            ));
        }

        // Stochastic Oscillator (14, 3, 3) - Simplified implementation
        int stochKPeriod = 14;
        int stochK1 = 3;
        int stochD1 = 3;
        try {
            StochasticOscillatorKIndicator stochasticK = new StochasticOscillatorKIndicator(series, stochKPeriod);
            if (series.getBarCount() > stochKPeriod + stochK1) {
                double stochKValue = stochasticK.getValue(series.getEndIndex()).doubleValue();
                String stochSignal = getStochasticSignal(stochKValue, stochKValue); // Simplified
                oscillators.add(new OscillatorIndicatorDTO(
                    "STOCH",
                    round(stochKValue, 2),
                    stochSignal,
                    String.format("Stochastic %%K (%d, %d, %d)", stochKPeriod, stochK1, stochD1)
                ));
            }
        } catch (Exception e) {
            // Skip if indicator cannot be calculated
        }

        // ADX (14)
        int adxPeriod = 14;
        ADXIndicator adx = new ADXIndicator(series, adxPeriod);
        if (series.getBarCount() > adxPeriod * 2) {
            double adxValue = adx.getValue(series.getEndIndex()).doubleValue();
            String adxSignal = adxValue > 25 ? "BUY" : adxValue > 20 ? "NEUTRAL" : "SELL";
            oscillators.add(new OscillatorIndicatorDTO(
                "ADX",
                round(adxValue, 2),
                adxSignal,
                String.format("Average Directional Index (%d)", adxPeriod)
            ));
        }

        // CCI (20)
        int cciPeriod = 20;
        CCIIndicator cci = new CCIIndicator(series, cciPeriod);
        if (series.getBarCount() > cciPeriod) {
            double cciValue = cci.getValue(series.getEndIndex()).doubleValue();
            String cciSignal = getCCISignal(cciValue);
            oscillators.add(new OscillatorIndicatorDTO(
                "CCI",
                round(cciValue, 2),
                cciSignal,
                String.format("Commodity Channel Index (%d)", cciPeriod)
            ));
        }

        return oscillators;
    }

    private List<MovingAverageIndicatorDTO> calculateMovingAverages(BarSeries series) {
        List<MovingAverageIndicatorDTO> movingAverages = new ArrayList<>();
        ClosePriceIndicator closePrice = new ClosePriceIndicator(series);
        VolumeIndicator volume = new VolumeIndicator(series);

        int period = 20; // All moving averages use period 20
        double currentPrice = closePrice.getValue(series.getEndIndex()).doubleValue();

        if (series.getBarCount() <= period) {
            return movingAverages; // Not enough data
        }

        // SMA indicator
        SMAIndicator sma = new SMAIndicator(closePrice, period);
        double smaValue = sma.getValue(series.getEndIndex()).doubleValue();
        String smaSignal = currentPrice > smaValue ? "BUY" : "SELL";
        movingAverages.add(new MovingAverageIndicatorDTO(
            "SMA",
            round(smaValue, 2),
            smaSignal,
            "Simple Moving Average"
        ));

        // EMA indicator
        EMAIndicator ema = new EMAIndicator(closePrice, period);
        double emaValue = ema.getValue(series.getEndIndex()).doubleValue();
        String emaSignal = currentPrice > emaValue ? "BUY" : "SELL";
        movingAverages.add(new MovingAverageIndicatorDTO(
            "EMA",
            round(emaValue, 2),
            emaSignal,
            "Exponential Moving Average"
        ));

        // WMA indicator
        WMAIndicator wma = new WMAIndicator(closePrice, period);
        double wmaValue = wma.getValue(series.getEndIndex()).doubleValue();
        String wmaSignal = currentPrice > wmaValue ? "BUY" : "SELL";
        movingAverages.add(new MovingAverageIndicatorDTO(
            "WMA",
            round(wmaValue, 2),
            wmaSignal,
            "Weighted Moving Average"
        ));

        // Bollinger Bands
        double bbMultiplier = 2.0;
        try {
            StandardDeviationIndicator stdDev = new StandardDeviationIndicator(closePrice, period);
            
            double middleValue = smaValue;
            double stdDevValue = stdDev.getValue(series.getEndIndex()).doubleValue();
            
            double upperValue = middleValue + (bbMultiplier * stdDevValue);
            double lowerValue = middleValue - (bbMultiplier * stdDevValue);
            
            movingAverages.add(new MovingAverageIndicatorDTO(
                "BB_UPPER",
                round(upperValue, 2),
                "SELL",
                "Bollinger Bands Upper"
            ));
            movingAverages.add(new MovingAverageIndicatorDTO(
                "BB_MIDDLE",
                round(middleValue, 2),
                "NEUTRAL",
                "Bollinger Bands Middle"
            ));
            movingAverages.add(new MovingAverageIndicatorDTO(
                "BB_LOWER",
                round(lowerValue, 2),
                "BUY",
                "Bollinger Bands Lower"
            ));
        } catch (Exception e) {
            // Skip if indicator cannot be calculated
        }

        // Volume Moving Average
        SMAIndicator volumeSMA = new SMAIndicator(volume, period);
        double volumeMaValue = volumeSMA.getValue(series.getEndIndex()).doubleValue();
        double currentVolume = volume.getValue(series.getEndIndex()).doubleValue();
        String volumeSignal = currentVolume > volumeMaValue ? "BUY" : "SELL";
        movingAverages.add(new MovingAverageIndicatorDTO(
            "VOLUME_SMA",
            round(volumeMaValue, 0),
            volumeSignal,
            "Volume Simple Moving Average"
        ));

        return movingAverages;
    }

    private String getRSISignal(double rsi) {
        if (rsi >= 70) return "SELL";
        if (rsi <= 30) return "BUY";
        return "NEUTRAL";
    }

    private String getStochasticSignal(double k, double d) {
        if (k >= 80 && d >= 80) return "SELL";
        if (k <= 20 && d <= 20) return "BUY";
        return "NEUTRAL";
    }

    private String getCCISignal(double cci) {
        if (cci > 100) return "SELL";
        if (cci < -100) return "BUY";
        return "NEUTRAL";
    }

    private TechnicalAnalysisResponseDTO.OscillatorSummary calculateOscillatorSummary(List<OscillatorIndicatorDTO> oscillators) {
        int buyCount = 0;
        int sellCount = 0;
        int neutralCount = 0;

        for (OscillatorIndicatorDTO osc : oscillators) {
            switch (osc.getSignal()) {
                case "BUY":
                    buyCount++;
                    break;
                case "SELL":
                    sellCount++;
                    break;
                default:
                    neutralCount++;
                    break;
            }
        }

        String overallSignal = "NEUTRAL";
        if (buyCount > sellCount + neutralCount) {
            overallSignal = buyCount > sellCount * 2 ? "STRONG_BUY" : "BUY";
        } else if (sellCount > buyCount + neutralCount) {
            overallSignal = sellCount > buyCount * 2 ? "STRONG_SELL" : "SELL";
        }

        return new TechnicalAnalysisResponseDTO.OscillatorSummary(overallSignal, buyCount, sellCount, neutralCount);
    }

    private TechnicalAnalysisResponseDTO.MovingAverageSummary calculateMovingAverageSummary(List<MovingAverageIndicatorDTO> movingAverages) {
        int buyCount = 0;
        int sellCount = 0;
        int neutralCount = 0;

        for (MovingAverageIndicatorDTO ma : movingAverages) {
            switch (ma.getSignal()) {
                case "BUY":
                    buyCount++;
                    break;
                case "SELL":
                    sellCount++;
                    break;
                default:
                    neutralCount++;
                    break;
            }
        }

        String overallSignal = "NEUTRAL";
        if (buyCount > sellCount + neutralCount) {
            overallSignal = buyCount > sellCount * 2 ? "STRONG_BUY" : "BUY";
        } else if (sellCount > buyCount + neutralCount) {
            overallSignal = sellCount > buyCount * 2 ? "STRONG_SELL" : "SELL";
        }

        return new TechnicalAnalysisResponseDTO.MovingAverageSummary(overallSignal, buyCount, sellCount, neutralCount);
    }

    private double round(double value, int decimals) {
        double multiplier = Math.pow(10, decimals);
        return Math.round(value * multiplier) / multiplier;
    }
}


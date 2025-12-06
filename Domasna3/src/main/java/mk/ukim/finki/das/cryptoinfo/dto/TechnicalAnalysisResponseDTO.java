package mk.ukim.finki.das.cryptoinfo.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class TechnicalAnalysisResponseDTO {
    private String symbol;
    private String timeframe; // DAILY, WEEKLY, MONTHLY
    private OscillatorSummary oscillatorSummary;
    private MovingAverageSummary movingAverageSummary;
    private List<OscillatorIndicatorDTO> oscillators;
    private List<MovingAverageIndicatorDTO> movingAverages;
    
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class OscillatorSummary {
        private String overallSignal; // STRONG_BUY, BUY, NEUTRAL, SELL, STRONG_SELL
        private int buyCount;
        private int sellCount;
        private int neutralCount;
    }
    
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class MovingAverageSummary {
        private String overallSignal; // STRONG_BUY, BUY, NEUTRAL, SELL, STRONG_SELL
        private int buyCount;
        private int sellCount;
        private int neutralCount;
    }
}


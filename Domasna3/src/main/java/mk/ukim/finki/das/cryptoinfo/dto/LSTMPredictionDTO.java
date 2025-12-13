package mk.ukim.finki.das.cryptoinfo.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class LSTMPredictionDTO {
    private String symbol;
    private Integer lookbackPeriod;
    private Integer trainingSamples;
    private Integer validationSamples;
    private Double lastPrice;
    private String lastDate;
    private MetricsDTO metrics;
    private List<PredictionDTO> predictions;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class MetricsDTO {
        private Double rmse;
        private Double mape;
        private Double r2Score;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class PredictionDTO {
        private String date;
        private Double predictedPrice;
    }
}




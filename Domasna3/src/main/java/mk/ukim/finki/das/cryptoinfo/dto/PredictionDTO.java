package mk.ukim.finki.das.cryptoinfo.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class PredictionDTO {
    private String symbol;
    
    @JsonProperty("predicted_close")
    private Double predicted_close;
}


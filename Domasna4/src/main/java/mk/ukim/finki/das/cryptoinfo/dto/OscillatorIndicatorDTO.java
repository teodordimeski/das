package mk.ukim.finki.das.cryptoinfo.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class OscillatorIndicatorDTO {
    private String name;
    private Double value;
    private String signal; // BUY, SELL, NEUTRAL
    private String displayName; // e.g., "Relative Strength Index (14)"
}


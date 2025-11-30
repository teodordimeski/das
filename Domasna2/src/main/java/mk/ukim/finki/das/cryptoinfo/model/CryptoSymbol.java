package mk.ukim.finki.das.cryptoinfo.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.validation.constraints.PositiveOrZero;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.time.LocalDate;

@Data
@Entity
@Table(name = "crypto_coins")
@NoArgsConstructor
@AllArgsConstructor
public class CryptoSymbol implements Serializable {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id", nullable = false)
    private Long id;

    @Column(name = "date", nullable = false)
    private LocalDate date;

    @Column(name = "open")
    @PositiveOrZero
    private Double open;

    @Column(name = "high")
    @PositiveOrZero
    private Double high;

    @Column(name = "low")
    @PositiveOrZero
    private Double low;

    @Column(name = "close")
    @PositiveOrZero
    private Double close;

    @Column(name = "volume")
    @PositiveOrZero
    private Double volume;

    @Column(name = "quoteAssetVolume")
    @PositiveOrZero
    private Double quoteAssetVolume;
    
    @Column(name = "symbol", nullable = false)
    private String symbol;

    @Column(name = "lastPrice_24h")
    @PositiveOrZero
    private Double lastPrice_24h;

    @Column(name = "volume_24h")
    @PositiveOrZero
    private Double volume_24h;

    @Column(name = "quoteVolume_24h")
    @PositiveOrZero
    private Double quoteVolume_24h;

    @Column(name = "high_24h")
    @PositiveOrZero
    private Double high_24h;

    @Column(name = "low_24h")
    @PositiveOrZero
    private Double low_24h;

    @Column(name = "baseAsset")
    private String baseAsset;

    @Column(name = "quoteAsset")
    private String quoteAsset;

    @Column(name = "symbolUsed", nullable = false)
    private String symbolUsed;

}

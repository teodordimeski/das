package mk.ukim.finki.das.cryptoinfo.repository;

import mk.ukim.finki.das.cryptoinfo.model.CryptoSymbol;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

@Repository
public interface CryptoSymbolInterface extends JpaRepository<CryptoSymbol, Long> {

    // Get rows for a symbol
    List<CryptoSymbol> findBySymbolIgnoreCase(String symbol);

    // Get rows for a symbol in a date range
    List<CryptoSymbol> findBySymbolIgnoreCaseAndDateBetween(
            String symbol,
            LocalDate from,
            LocalDate to
    );

    // OPTIONAL: search by LIKE
    @Query("""
           SELECT DISTINCT c.symbol
           FROM CryptoSymbol c
           WHERE LOWER(c.symbol) LIKE LOWER(CONCAT('%', :query, '%'))
           """)
    List<String> searchSymbols(@Param("query") String query);

    // Find by primary key (explicitly declared for clarity)
    Optional<CryptoSymbol> findById(Long id);
}


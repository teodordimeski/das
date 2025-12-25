package mk.ukim.finki.das.cryptoinfo.services;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import mk.ukim.finki.das.cryptoinfo.model.CryptoSymbol;
import org.springframework.data.domain.Pageable;

public interface CryptoSymbolService {

    List<CryptoSymbol> getAllData(Pageable pageable);

    List<CryptoSymbol> findBySymbol(String symbol);

    List<CryptoSymbol> findBySymbolsAndDate(String symbol, LocalDate fromDate, LocalDate toDate);

    Optional<CryptoSymbol> findById(Long id);

    List<String> searchSymbols(String query);

}



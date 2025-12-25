package mk.ukim.finki.das.cryptoinfo.services;

import mk.ukim.finki.das.cryptoinfo.model.CryptoSymbol;
import mk.ukim.finki.das.cryptoinfo.repository.CryptoSymbolInterface;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

@Service
public class CryptoSymbolServiceImpl implements CryptoSymbolService {

    private final CryptoSymbolInterface cryptoSymbolRepository;

    public CryptoSymbolServiceImpl(CryptoSymbolInterface cryptoSymbolRepository) {
        this.cryptoSymbolRepository = cryptoSymbolRepository;
    }

    @Override
    public List<CryptoSymbol> getAllData(Pageable pageable) {
        return cryptoSymbolRepository.findAll(pageable).getContent();
    }

    @Override
    public List<CryptoSymbol> findBySymbol(String symbol) {
        return cryptoSymbolRepository.findBySymbolIgnoreCase(symbol);
    }

    @Override
    public List<CryptoSymbol> findBySymbolsAndDate(String symbol, LocalDate fromDate, LocalDate toDate) {
        return cryptoSymbolRepository.findBySymbolIgnoreCaseAndDateBetween(symbol, fromDate, toDate);
    }

    @Override
    public Optional<CryptoSymbol> findById(Long id) {
        return cryptoSymbolRepository.findById(id);
    }

    @Override
    public List<String> searchSymbols(String query) {
        return cryptoSymbolRepository.searchSymbols(query);
    }
}

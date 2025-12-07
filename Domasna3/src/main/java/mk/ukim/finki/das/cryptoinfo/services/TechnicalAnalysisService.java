package mk.ukim.finki.das.cryptoinfo.services;

import mk.ukim.finki.das.cryptoinfo.dto.TechnicalAnalysisResponseDTO;
import mk.ukim.finki.das.cryptoinfo.model.CryptoSymbol;

import java.util.List;

public interface TechnicalAnalysisService {
    TechnicalAnalysisResponseDTO getTechnicalAnalysis(String symbol, String timeframe);
    List<CryptoSymbol> aggregateByTimeframe(List<CryptoSymbol> data, String timeframe);
}


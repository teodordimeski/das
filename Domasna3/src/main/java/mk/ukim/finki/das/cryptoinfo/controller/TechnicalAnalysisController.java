package mk.ukim.finki.das.cryptoinfo.controller;

import mk.ukim.finki.das.cryptoinfo.dto.TechnicalAnalysisResponseDTO;
import mk.ukim.finki.das.cryptoinfo.services.TechnicalAnalysisService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/technical")
@CrossOrigin(origins = "http://localhost:3000")
public class TechnicalAnalysisController {

    private static final Logger logger = LoggerFactory.getLogger(TechnicalAnalysisController.class);
    private final TechnicalAnalysisService technicalAnalysisService;

    public TechnicalAnalysisController(TechnicalAnalysisService technicalAnalysisService) {
        this.technicalAnalysisService = technicalAnalysisService;
    }

    /**
     * GET technical analysis for a symbol with a specific timeframe
     * URL: GET http://localhost:8080/api/technical/{symbol}?timeframe=DAILY|WEEKLY|MONTHLY
     * Example: GET http://localhost:8080/api/technical/BTCUSDT?timeframe=MONTHLY
     */
    @GetMapping("/{symbol}")
    public ResponseEntity<TechnicalAnalysisResponseDTO> getTechnicalAnalysis(
            @PathVariable String symbol,
            @RequestParam(value = "timeframe", defaultValue = "MONTHLY") String timeframe
    ) {
        try {
            logger.info("GET /api/technical/{} - timeframe: {}", symbol, timeframe);
            
            // Validate timeframe
            if (!isValidTimeframe(timeframe)) {
                return new ResponseEntity<>(HttpStatus.BAD_REQUEST);
            }
            
            TechnicalAnalysisResponseDTO result = technicalAnalysisService.getTechnicalAnalysis(symbol, timeframe.toUpperCase());
            logger.info("GET /api/technical/{} - returned analysis with {} oscillators and {} moving averages", 
                    symbol, result.getOscillators().size(), result.getMovingAverages().size());
            
            return new ResponseEntity<>(result, HttpStatus.OK);
        } catch (IllegalArgumentException e) {
            logger.error("Error in getTechnicalAnalysis for {}: {}", symbol, e.getMessage());
            return new ResponseEntity<>(HttpStatus.BAD_REQUEST);
        } catch (Exception e) {
            logger.error("Error in getTechnicalAnalysis for {}: ", symbol, e);
            return new ResponseEntity<>(HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    private boolean isValidTimeframe(String timeframe) {
        if (timeframe == null) return false;
        String upper = timeframe.toUpperCase();
        return "DAILY".equals(upper) || "WEEKLY".equals(upper) || "MONTHLY".equals(upper);
    }
}


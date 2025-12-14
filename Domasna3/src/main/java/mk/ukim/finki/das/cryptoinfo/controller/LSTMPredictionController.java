package mk.ukim.finki.das.cryptoinfo.controller;

import mk.ukim.finki.das.cryptoinfo.dto.LSTMPredictionDTO;
import mk.ukim.finki.das.cryptoinfo.services.LSTMPredictionService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/lstm")
@CrossOrigin(origins = "http://localhost:3000")
public class LSTMPredictionController {

    private static final Logger logger = LoggerFactory.getLogger(LSTMPredictionController.class);
    private final LSTMPredictionService lstmPredictionService;

    public LSTMPredictionController(LSTMPredictionService lstmPredictionService) {
        this.lstmPredictionService = lstmPredictionService;
    }

    /**
     * GET LSTM price prediction for a symbol
     * URL: GET http://localhost:8080/api/lstm/{symbol}?lookback=60&days=1
     * Example: GET http://localhost:8080/api/lstm/BTCUSDT?lookback=60&days=1
     */
    @GetMapping("/{symbol}")
    public ResponseEntity<LSTMPredictionDTO> getLSTMPrediction(
            @PathVariable String symbol,
            @RequestParam(value = "lookback", required = false) Integer lookbackPeriod,
            @RequestParam(value = "days", required = false) Integer predictionDays
    ) {
        try {
            logger.info("GET /api/lstm/{} - lookback: {}, days: {}", symbol, lookbackPeriod, predictionDays);
            
            // Default values
            if (lookbackPeriod == null) {
                lookbackPeriod = 30; // Default lookback period
            }
            if (predictionDays == null) {
                predictionDays = 7; // Default prediction days
            }
            
            // Validate parameters
            if (lookbackPeriod < 10 || lookbackPeriod > 100) {
                return new ResponseEntity<>(HttpStatus.BAD_REQUEST);
            }
            if (predictionDays < 1 || predictionDays > 30) {
                return new ResponseEntity<>(HttpStatus.BAD_REQUEST);
            }
            
            LSTMPredictionDTO result = lstmPredictionService.getLSTMPrediction(
                    symbol.toUpperCase(), lookbackPeriod, predictionDays);
            
            logger.info("GET /api/lstm/{} - returned prediction with {} future days", 
                    symbol, result.getPredictions().size());
            
            return new ResponseEntity<>(result, HttpStatus.OK);
            
        } catch (IllegalArgumentException e) {
            logger.error("Error in getLSTMPrediction for {}: {}", symbol, e.getMessage());
            return new ResponseEntity<>(HttpStatus.BAD_REQUEST);
        } catch (Exception e) {
            logger.error("Error in getLSTMPrediction for {}: ", symbol, e);
            return new ResponseEntity<>(HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
}





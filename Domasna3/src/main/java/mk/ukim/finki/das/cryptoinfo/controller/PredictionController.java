package mk.ukim.finki.das.cryptoinfo.controller;

import mk.ukim.finki.das.cryptoinfo.dto.PredictionDTO;
import mk.ukim.finki.das.cryptoinfo.services.PredictionService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/predictions")
@CrossOrigin(origins = "http://localhost:3000")
public class PredictionController {

    private static final Logger logger = LoggerFactory.getLogger(PredictionController.class);
    private final PredictionService predictionService;

    public PredictionController(PredictionService predictionService) {
        this.predictionService = predictionService;
    }

    /**
     * GET price prediction for a symbol
     * URL: GET http://localhost:8080/api/predictions/BTC
     * URL: GET http://localhost:8080/api/predictions/BTCUSDT
     * Example: GET http://localhost:8080/api/predictions/BTC
     */
    @GetMapping("/{symbol}")
    public ResponseEntity<PredictionDTO> getPrediction(
            @PathVariable String symbol
    ) {
        try {
            logger.info("GET /api/predictions/{}", symbol);
            
            if (symbol == null || symbol.trim().isEmpty()) {
                return new ResponseEntity<>(HttpStatus.BAD_REQUEST);
            }
            
            PredictionDTO result = predictionService.getPrediction(symbol);
            
            logger.info("GET /api/predictions/{} - returned prediction: {}", 
                    symbol, result.getPredicted_close());
            
            return new ResponseEntity<>(result, HttpStatus.OK);
            
        } catch (IllegalArgumentException e) {
            logger.error("Error in getPrediction for {}: {}", symbol, e.getMessage());
            return new ResponseEntity<>(HttpStatus.BAD_REQUEST);
        } catch (Exception e) {
            logger.error("Error in getPrediction for {}: ", symbol, e);
            return new ResponseEntity<>(HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
}


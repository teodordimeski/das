package mk.ukim.finki.das.cryptoinfo.controller;

import mk.ukim.finki.das.cryptoinfo.model.CryptoSymbol;
import mk.ukim.finki.das.cryptoinfo.services.CryptoSymbolService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "http://localhost:3000")
public class CryptoSymbolController {

    private static final Logger logger = LoggerFactory.getLogger(CryptoSymbolController.class);
    private final CryptoSymbolService cryptoService;

    public CryptoSymbolController(CryptoSymbolService cryptoService) {
        this.cryptoService = cryptoService;
    }

    // ----------------------------------------------------
    // HEALTH CHECK / TEST ENDPOINT
    // URL: GET http://localhost:8080/api/health
    // ----------------------------------------------------
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> healthCheck() {
        Map<String, Object> response = new HashMap<>();
        try {
            long count = cryptoService.getAllData(PageRequest.of(0, 1)).size();
            response.put("status", "UP");
            response.put("database", "connected");
            response.put("recordsAvailable", count > 0);
            logger.info("Health check: Database connected, records available: {}", count > 0);
            return new ResponseEntity<>(response, HttpStatus.OK);
        } catch (Exception e) {
            response.put("status", "DOWN");
            response.put("error", e.getMessage());
            logger.error("Health check failed: ", e);
            return new ResponseEntity<>(response, HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    // ----------------------------------------------------
    // GET ALL DATA (root endpoint) - with pagination to prevent crashes
    // URL: GET http://localhost:8080/api
    // URL: GET http://localhost:8080/api?page=0&size=100
    // ----------------------------------------------------
    @GetMapping("")
    public ResponseEntity<List<CryptoSymbol>> getAllData(
            @RequestParam(value = "page", defaultValue = "0") int page,
            @RequestParam(value = "size", defaultValue = "1000000") int size
    ) {
        try {
            logger.info("GET /api - page: {}, size: {}", page, size);
            // Limit max size to prevent crashes (max 10000 records per request)
            int safeSize = Math.min(size, 10000);
            Pageable pageable = PageRequest.of(page, safeSize);
            List<CryptoSymbol> result = cryptoService.getAllData(pageable);
            logger.info("GET /api - returned {} records", result.size());
            return new ResponseEntity<>(result, HttpStatus.OK);
        } catch (Exception e) {
            logger.error("Error in getAllData: ", e);
            return new ResponseEntity<>(HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    // ----------------------------------------------------
    // GET ALL DATA (alternative endpoint) - with pagination
    // URL: GET http://localhost:8080/api/all
    // URL: GET http://localhost:8080/api/all?page=0&size=100
    // ----------------------------------------------------
    @GetMapping("/all")
    public ResponseEntity<List<CryptoSymbol>> getAllDataAlternative(
            @RequestParam(value = "page", defaultValue = "0") int page,
            @RequestParam(value = "size", defaultValue = "1000000") int size
    ) {
        // Limit max size to prevent crashes (max 10000 records per request)
        int safeSize = Math.min(size, 10000);
        Pageable pageable = PageRequest.of(page, safeSize);
        List<CryptoSymbol> result = cryptoService.getAllData(pageable);
        return new ResponseEntity<>(result, HttpStatus.OK);
    }

    // ----------------------------------------------------
    // GET BY SYMBOL (with optional date range)
    // URL: GET http://localhost:8080/api/symbol/BTCUSDT
    // URL: GET http://localhost:8080/api/symbol/BTCUSDT?from=2024-01-01&to=2024-01-31
    // ----------------------------------------------------
    @GetMapping("/symbol/{symbol}")
    public ResponseEntity<List<CryptoSymbol>> getBySymbol(
            @PathVariable String symbol,
            @RequestParam(value = "from", required = false) String from,
            @RequestParam(value = "to", required = false) String to
    ) {
        try {
            logger.info("GET /api/symbol/{} - from: {}, to: {}", symbol, from, to);
            // If date range parameters are provided, filter by date range
            if (from != null && to != null) {
                LocalDate fromDate = LocalDate.parse(from);
                LocalDate toDate = LocalDate.parse(to);
                List<CryptoSymbol> result =
                        cryptoService.findBySymbolsAndDate(symbol, fromDate, toDate);
                logger.info("GET /api/symbol/{} - returned {} records (date range)", symbol, result.size());
                return new ResponseEntity<>(result, HttpStatus.OK);
            }
            
            // Otherwise, return all data for the symbol
            List<CryptoSymbol> result = cryptoService.findBySymbol(symbol);
            logger.info("GET /api/symbol/{} - returned {} records", symbol, result.size());
            return new ResponseEntity<>(result, HttpStatus.OK);
        } catch (Exception e) {
            logger.error("Error in getBySymbol for {}: ", symbol, e);
            return new ResponseEntity<>(HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    // ----------------------------------------------------
    // GET BY ID
    // URL: GET http://localhost:8080/api/id/1
    // Returns a single CryptoSymbol by its ID (primary key)
    // ----------------------------------------------------
    @GetMapping("/id/{id}")
    public ResponseEntity<CryptoSymbol> getById(@PathVariable Long id) {
        return cryptoService.findById(id)
                .map(cryptoSymbol -> new ResponseEntity<>(cryptoSymbol, HttpStatus.OK))
                .orElse(new ResponseEntity<>(HttpStatus.NOT_FOUND));
    }

    // ----------------------------------------------------
    // SEARCH SYMBOLS (fuzzy search)
    // URL: GET http://localhost:8080/api/search?query=BTC
    // URL: GET http://localhost:8080/api/search?query=USDT
    // Returns a list of distinct symbol names that match the query (case-insensitive)
    // Useful for autocomplete or finding available symbols
    // ----------------------------------------------------
    @GetMapping("/search")
    public ResponseEntity<List<String>> searchSymbols(
            @RequestParam("query") String query
    ) {
        List<String> result = cryptoService.searchSymbols(query);
        return new ResponseEntity<>(result, HttpStatus.OK);
    }

    // ----------------------------------------------------
    // OPTIONAL: DELETE ALL RECORDS FOR A SYMBOL
    // Example:
    // DELETE http://localhost:8080/api/symbol/BTCUSDT
    // ----------------------------------------------------
    // @DeleteMapping("/symbol/{symbol}")
    // public ResponseEntity<String> deleteSymbol(
    //         @PathVariable String symbol
    // ) {
    //     List<CryptoSymbol> items = cryptoService.findBySymbol(symbol);

    //     if (items.isEmpty()) {
    //         return new ResponseEntity<>("Symbol not found", HttpStatus.NOT_FOUND);
    //     }

    //     // delete manually (your repo must have this method)
    //     // cryptoService.deleteBySymbol(symbol);

    //     return new ResponseEntity<>("Deleted successfully", HttpStatus.OK);
    // }
}

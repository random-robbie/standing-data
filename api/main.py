import os
import csv
import glob
from typing import List, Optional, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import pandas as pd
from pydantic import BaseModel


class Aircraft(BaseModel):
    icao: str
    registration: str
    model_icao: str
    manufacturer: str
    model: str
    manufacturer_and_model: str
    is_private_operator: int
    operator: str
    airline_code: str
    serial_number: str
    year_built: Optional[int]


class Airline(BaseModel):
    code: str
    name: str
    icao: str
    iata: str
    positioning_flight_pattern: str
    charter_flight_pattern: str


class Airport(BaseModel):
    code: str
    name: str
    icao: str
    iata: str
    location: str
    country_iso2: str
    latitude: Optional[float]
    longitude: Optional[float]
    altitude_feet: Optional[int]


class Route(BaseModel):
    callsign: str
    code: str
    number: str
    airline_code: str
    airport_codes: str


class Country(BaseModel):
    iso: str
    name: str


class ModelType(BaseModel):
    icao: str
    manufacturer: str
    model: str
    engines: str
    engine_type_code: str
    engine_placement_code: str
    species_code: str
    wake_turbulence_code: str
    is_active: int


class CodeBlock(BaseModel):
    start: str
    finish: str
    count: int
    bitmask: str
    significant_bitmask: str
    is_military: int
    country_iso2: str


class RegistrationPrefix(BaseModel):
    prefix: str
    country_iso2: str
    has_hyphen: int
    decode_full_regex: str
    decode_no_hyphen_regex: str
    format_template: str


app = FastAPI(
    title="Aviation Standing Data API",
    description="FastAPI service for querying aviation standing data including aircraft, airlines, airports, and routes",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DataLoader:
    def __init__(self, data_path: str = "/data"):
        self.data_path = Path(data_path)
        self._airlines_cache = None
        self._countries_cache = None
        self._model_types_cache = None
        self._code_blocks_cache = None
        self._registration_prefixes_cache = None
        
    def load_airlines(self) -> List[Dict[str, Any]]:
        if self._airlines_cache is None:
            airlines_file = self.data_path / "airlines/schema-01/airlines.csv"
            self._airlines_cache = self._load_csv(airlines_file)
        return self._airlines_cache
    
    def load_countries(self) -> List[Dict[str, Any]]:
        if self._countries_cache is None:
            countries_file = self.data_path / "countries/schema-01/countries.csv"
            self._countries_cache = self._load_csv(countries_file)
        return self._countries_cache
    
    def load_model_types(self) -> List[Dict[str, Any]]:
        if self._model_types_cache is None:
            model_files = glob.glob(str(self.data_path / "model-type/schema-01/*.csv"))
            all_models = []
            for file_path in model_files:
                models = self._load_csv(file_path)
                all_models.extend(models)
            self._model_types_cache = all_models
        return self._model_types_cache
    
    def load_code_blocks(self) -> List[Dict[str, Any]]:
        if self._code_blocks_cache is None:
            code_blocks_file = self.data_path / "code-blocks/schema-01/code-blocks.csv"
            self._code_blocks_cache = self._load_csv(code_blocks_file)
        return self._code_blocks_cache
    
    def load_registration_prefixes(self) -> List[Dict[str, Any]]:
        if self._registration_prefixes_cache is None:
            reg_prefixes_file = self.data_path / "registration-prefixes/schema-01/reg-prefixes.csv"
            self._registration_prefixes_cache = self._load_csv(reg_prefixes_file)
        return self._registration_prefixes_cache
    
    def _load_csv(self, file_path: str | Path) -> List[Dict[str, Any]]:
        try:
            with open(file_path, 'r', encoding='utf-8-sig', newline='') as f:
                reader = csv.DictReader(f)
                return [row for row in reader]
        except FileNotFoundError:
            return []
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return []
    
    def search_aircraft(self, icao: Optional[str] = None, registration: Optional[str] = None, 
                       operator: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        results = []
        count = 0
        
        # Search through aircraft files
        aircraft_dirs = glob.glob(str(self.data_path / "aircraft/schema-01/*/*"))
        
        for dir_path in aircraft_dirs[:50]:  # Limit directories to search for performance
            if count >= limit:
                break
                
            csv_files = glob.glob(f"{dir_path}/*.csv")
            for csv_file in csv_files:
                if count >= limit:
                    break
                    
                aircraft_data = self._load_csv(csv_file)
                for aircraft in aircraft_data:
                    if count >= limit:
                        break
                        
                    match = True
                    if icao and icao.upper() not in aircraft.get('ICAO', '').upper():
                        match = False
                    if registration and registration.upper() not in aircraft.get('Registration', '').upper():
                        match = False
                    if operator and operator.upper() not in aircraft.get('Operator', '').upper():
                        match = False
                    
                    if match:
                        results.append(aircraft)
                        count += 1
        
        return results
    
    def search_airports(self, code: Optional[str] = None, icao: Optional[str] = None, 
                       iata: Optional[str] = None, name: Optional[str] = None, 
                       country: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        results = []
        count = 0
        
        # Search through airport files
        airport_dirs = glob.glob(str(self.data_path / "airports/schema-01/*"))
        
        for dir_path in airport_dirs:
            if count >= limit:
                break
                
            csv_files = glob.glob(f"{dir_path}/*.csv")
            for csv_file in csv_files:
                if count >= limit:
                    break
                    
                airport_data = self._load_csv(csv_file)
                for airport in airport_data:
                    if count >= limit:
                        break
                        
                    match = True
                    
                    # Check code (matches either Code field, ICAO, or IATA)
                    if code:
                        code_upper = code.upper()
                        airport_code = airport.get('Code', '').upper()
                        airport_icao = airport.get('ICAO', '').upper()
                        airport_iata = airport.get('IATA', '').upper()
                        
                        if (code_upper not in airport_code and 
                            code_upper not in airport_icao and 
                            code_upper not in airport_iata):
                            match = False
                    
                    # Check specific ICAO code
                    if icao and icao.upper() not in airport.get('ICAO', '').upper():
                        match = False
                    
                    # Check specific IATA code
                    if iata and iata.upper() not in airport.get('IATA', '').upper():
                        match = False
                    
                    # Check name
                    if name and name.upper() not in airport.get('Name', '').upper():
                        match = False
                    
                    # Check country
                    if country and country.upper() not in airport.get('CountryISO2', '').upper():
                        match = False
                    
                    if match:
                        results.append(airport)
                        count += 1
        
        return results
    
    def search_routes(self, callsign: Optional[str] = None, code: Optional[str] = None, 
                     airline_code: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        results = []
        count = 0
        
        # Search through route files
        route_dirs = glob.glob(str(self.data_path / "routes/schema-01/*"))
        
        for dir_path in route_dirs[:10]:  # Limit for performance
            if count >= limit:
                break
                
            csv_files = glob.glob(f"{dir_path}/*.csv")
            for csv_file in csv_files:
                if count >= limit:
                    break
                    
                route_data = self._load_csv(csv_file)
                for route in route_data:
                    if count >= limit:
                        break
                        
                    match = True
                    if callsign and callsign.upper() not in route.get('Callsign', '').upper():
                        match = False
                    if code and code.upper() not in route.get('Code', '').upper():
                        match = False
                    if airline_code and airline_code.upper() not in route.get('AirlineCode', '').upper():
                        match = False
                    
                    if match:
                        results.append(route)
                        count += 1
        
        return results


# Initialize data loader
data_loader = DataLoader()


# Static files and HTML frontend
# app.mount("/static", StaticFiles(directory="/app/static"), name="static")  # Commented out - no static files needed


@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Aviation Standing Data API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; margin-bottom: 30px; }
            .search-section { margin-bottom: 30px; padding: 20px; background: #ecf0f1; border-radius: 5px; }
            .search-form { display: flex; gap: 10px; margin-bottom: 15px; flex-wrap: wrap; }
            input, select, button { padding: 8px 12px; border: 1px solid #bdc3c7; border-radius: 4px; }
            button { background: #3498db; color: white; cursor: pointer; border: none; }
            button:hover { background: #2980b9; }
            .results { margin-top: 20px; }
            .result-item { background: white; border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
            .endpoint { margin: 20px 0; padding: 15px; background: #e8f4f8; border-radius: 5px; }
            .loading { text-align: center; padding: 20px; color: #7f8c8d; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛩️ Aviation Standing Data API</h1>
            <p>Search aviation data including aircraft, airlines, airports, and routes from Virtual Radar Server users.</p>
            
            <div class="search-section">
                <h3>🛬 Aircraft Search</h3>
                <div class="search-form">
                    <input type="text" id="aircraft-icao" placeholder="ICAO Code">
                    <input type="text" id="aircraft-registration" placeholder="Registration">
                    <input type="text" id="aircraft-operator" placeholder="Operator">
                    <button onclick="searchAircraft()">Search Aircraft</button>
                </div>
                <div id="aircraft-results" class="results"></div>
            </div>
            
            <div class="search-section">
                <h3>✈️ Airport Search</h3>
                <div class="search-form">
                    <input type="text" id="airport-code" placeholder="Any Code (ICAO/IATA)">
                    <input type="text" id="airport-icao" placeholder="ICAO Code (e.g. EGLL)">
                    <input type="text" id="airport-iata" placeholder="IATA Code (e.g. LHR)">
                    <input type="text" id="airport-name" placeholder="Airport Name">
                    <input type="text" id="airport-country" placeholder="Country Code">
                    <button onclick="searchAirports()">Search Airports</button>
                </div>
                <div id="airport-results" class="results"></div>
            </div>
            
            <div class="search-section">
                <h3>🛫 Airlines</h3>
                <button onclick="loadAirlines()">Load Airlines</button>
                <div id="airline-results" class="results"></div>
            </div>
            
            <div class="search-section">
                <h3>🔢 Code Blocks</h3>
                <button onclick="loadCodeBlocks()">Load Code Blocks</button>
                <div id="codeblocks-results" class="results"></div>
            </div>
            
            <div class="search-section">
                <h3>🏷️ Registration Prefixes</h3>
                <button onclick="loadRegistrationPrefixes()">Load Registration Prefixes</button>
                <div id="regprefixes-results" class="results"></div>
            </div>
            
            <div class="endpoint">
                <h3>📚 API Endpoints</h3>
                <ul>
                    <li><strong>GET /aircraft</strong> - Search aircraft (query: icao, registration, operator, limit)</li>
                    <li><strong>GET /airlines</strong> - Get all airlines</li>
                    <li><strong>GET /airports</strong> - Search airports (query: code, icao, iata, name, country, limit)</li>
                    <li><strong>GET /routes</strong> - Search routes (query: callsign, code, airline_code, limit)</li>
                    <li><strong>GET /countries</strong> - Get all countries</li>
                    <li><strong>GET /model-types</strong> - Get all model types</li>
                    <li><strong>GET /code-blocks</strong> - Get all Mode-S code blocks</li>
                    <li><strong>GET /registration-prefixes</strong> - Get all registration prefixes</li>
                    <li><strong>GET /docs</strong> - Interactive API documentation</li>
                </ul>
            </div>
        </div>
        
        <script>
            async function searchAircraft() {
                const icao = document.getElementById('aircraft-icao').value;
                const registration = document.getElementById('aircraft-registration').value;
                const operator = document.getElementById('aircraft-operator').value;
                
                const params = new URLSearchParams();
                if (icao) params.append('icao', icao);
                if (registration) params.append('registration', registration);
                if (operator) params.append('operator', operator);
                params.append('limit', '20');
                
                const resultsDiv = document.getElementById('aircraft-results');
                resultsDiv.innerHTML = '<div class="loading">Searching...</div>';
                
                try {
                    const response = await fetch(`/aircraft?${params}`);
                    const data = await response.json();
                    
                    if (data.length === 0) {
                        resultsDiv.innerHTML = '<p>No aircraft found.</p>';
                        return;
                    }
                    
                    let html = `<h4>Found ${data.length} aircraft:</h4>`;
                    data.forEach(aircraft => {
                        html += `
                            <div class="result-item">
                                <strong>${aircraft.Registration || 'N/A'}</strong> - ${aircraft.ManufacturerAndModel || 'N/A'}
                                <br>ICAO: ${aircraft.ICAO}, Operator: ${aircraft.Operator || 'N/A'}
                                <br>Year: ${aircraft.YearBuilt || 'N/A'}
                            </div>
                        `;
                    });
                    resultsDiv.innerHTML = html;
                } catch (error) {
                    resultsDiv.innerHTML = '<p>Error searching aircraft: ' + error.message + '</p>';
                }
            }
            
            async function searchAirports() {
                const code = document.getElementById('airport-code').value;
                const icao = document.getElementById('airport-icao').value;
                const iata = document.getElementById('airport-iata').value;
                const name = document.getElementById('airport-name').value;
                const country = document.getElementById('airport-country').value;
                
                const params = new URLSearchParams();
                if (code) params.append('code', code);
                if (icao) params.append('icao', icao);
                if (iata) params.append('iata', iata);
                if (name) params.append('name', name);
                if (country) params.append('country', country);
                params.append('limit', '20');
                
                const resultsDiv = document.getElementById('airport-results');
                resultsDiv.innerHTML = '<div class="loading">Searching...</div>';
                
                try {
                    const response = await fetch(`/airports?${params}`);
                    const data = await response.json();
                    
                    if (data.length === 0) {
                        resultsDiv.innerHTML = '<p>No airports found.</p>';
                        return;
                    }
                    
                    let html = `<h4>Found ${data.length} airports:</h4>`;
                    data.forEach(airport => {
                        html += `
                            <div class="result-item">
                                <strong>${airport.Code}</strong> - ${airport.Name || 'N/A'}
                                <br>ICAO: ${airport.ICAO || 'N/A'}, IATA: ${airport.IATA || 'N/A'}
                                <br>Location: ${airport.Location || 'N/A'}, Country: ${airport.CountryISO2 || 'N/A'}
                                <br>Coordinates: ${airport.Latitude || 'N/A'}, ${airport.Longitude || 'N/A'}
                            </div>
                        `;
                    });
                    resultsDiv.innerHTML = html;
                } catch (error) {
                    resultsDiv.innerHTML = '<p>Error searching airports: ' + error.message + '</p>';
                }
            }
            
            async function loadAirlines() {
                const resultsDiv = document.getElementById('airline-results');
                resultsDiv.innerHTML = '<div class="loading">Loading airlines...</div>';
                
                try {
                    const response = await fetch('/airlines');
                    const data = await response.json();
                    
                    let html = `<h4>Airlines (${data.length} total):</h4>`;
                    data.slice(0, 50).forEach(airline => {
                        html += `
                            <div class="result-item">
                                <strong>${airline.Code}</strong> - ${airline.Name || 'N/A'}
                                <br>ICAO: ${airline.ICAO || 'N/A'}, IATA: ${airline.IATA || 'N/A'}
                            </div>
                        `;
                    });
                    if (data.length > 50) {
                        html += '<p><em>Showing first 50 airlines only</em></p>';
                    }
                    resultsDiv.innerHTML = html;
                } catch (error) {
                    resultsDiv.innerHTML = '<p>Error loading airlines: ' + error.message + '</p>';
                }
            }
            
            async function loadCodeBlocks() {
                const resultsDiv = document.getElementById('codeblocks-results');
                resultsDiv.innerHTML = '<div class="loading">Loading code blocks...</div>';
                
                try {
                    const response = await fetch('/code-blocks');
                    const data = await response.json();
                    
                    let html = `<h4>Code Blocks (${data.length} total):</h4>`;
                    data.slice(0, 20).forEach(block => {
                        html += `
                            <div class="result-item">
                                <strong>${block.Start}-${block.Finish}</strong> (${block.Count} codes)
                                <br>Country: ${block.CountryISO2}, Military: ${block.IsMilitary === '1' ? 'Yes' : 'No'}
                                <br>Bitmask: ${block.Bitmask}, Significant: ${block.SignificantBitmask}
                            </div>
                        `;
                    });
                    if (data.length > 20) {
                        html += '<p><em>Showing first 20 code blocks only</em></p>';
                    }
                    resultsDiv.innerHTML = html;
                } catch (error) {
                    resultsDiv.innerHTML = '<p>Error loading code blocks: ' + error.message + '</p>';
                }
            }
            
            async function loadRegistrationPrefixes() {
                const resultsDiv = document.getElementById('regprefixes-results');
                resultsDiv.innerHTML = '<div class="loading">Loading registration prefixes...</div>';
                
                try {
                    const response = await fetch('/registration-prefixes');
                    const data = await response.json();
                    
                    let html = `<h4>Registration Prefixes (${data.length} total):</h4>`;
                    data.slice(0, 50).forEach(prefix => {
                        html += `
                            <div class="result-item">
                                <strong>${prefix.Prefix}</strong> - ${prefix.CountryISO2}
                                <br>Format: ${prefix.FormatTemplate}
                                <br>Hyphen: ${prefix.HasHyphen === '1' ? 'Yes' : 'No'}
                            </div>
                        `;
                    });
                    if (data.length > 50) {
                        html += '<p><em>Showing first 50 prefixes only</em></p>';
                    }
                    resultsDiv.innerHTML = html;
                } catch (error) {
                    resultsDiv.innerHTML = '<p>Error loading registration prefixes: ' + error.message + '</p>';
                }
            }
        </script>
    </body>
    </html>
    """


@app.get("/aircraft")
async def get_aircraft(
    icao: Optional[str] = Query(None, description="Search by ICAO code"),
    registration: Optional[str] = Query(None, description="Search by registration"),
    operator: Optional[str] = Query(None, description="Search by operator"),
    limit: int = Query(100, description="Maximum number of results", le=1000)
):
    try:
        results = data_loader.search_aircraft(icao, registration, operator, limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching aircraft: {str(e)}")


@app.get("/airlines")
async def get_airlines():
    try:
        airlines = data_loader.load_airlines()
        return airlines
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading airlines: {str(e)}")


@app.get("/airports")
async def get_airports(
    code: Optional[str] = Query(None, description="Search by any airport code (ICAO, IATA, or Code)"),
    icao: Optional[str] = Query(None, description="Search by specific ICAO code"),
    iata: Optional[str] = Query(None, description="Search by specific IATA code"),
    name: Optional[str] = Query(None, description="Search by airport name"),
    country: Optional[str] = Query(None, description="Search by country ISO2 code"),
    limit: int = Query(100, description="Maximum number of results", le=1000)
):
    try:
        results = data_loader.search_airports(code, icao, iata, name, country, limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching airports: {str(e)}")


@app.get("/routes")
async def get_routes(
    callsign: Optional[str] = Query(None, description="Search by callsign"),
    code: Optional[str] = Query(None, description="Search by airline code"),
    airline_code: Optional[str] = Query(None, description="Search by airline code"),
    limit: int = Query(100, description="Maximum number of results", le=1000)
):
    try:
        results = data_loader.search_routes(callsign, code, airline_code, limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching routes: {str(e)}")


@app.get("/countries")
async def get_countries():
    try:
        countries = data_loader.load_countries()
        return countries
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading countries: {str(e)}")


@app.get("/model-types")
async def get_model_types():
    try:
        model_types = data_loader.load_model_types()
        return model_types
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading model types: {str(e)}")


@app.get("/code-blocks")
async def get_code_blocks():
    try:
        code_blocks = data_loader.load_code_blocks()
        return code_blocks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading code blocks: {str(e)}")


@app.get("/registration-prefixes")
async def get_registration_prefixes():
    try:
        reg_prefixes = data_loader.load_registration_prefixes()
        return reg_prefixes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading registration prefixes: {str(e)}")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Aviation Standing Data API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
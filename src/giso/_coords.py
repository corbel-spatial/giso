import functools
import math
import re
from typing import Any

import pyproj

_BANDS = "CDEFGHJKLMNPQRSTUVWX"
_MGRS_COL_SETS = [
    "ABCDEFGH",  # zones 1, 4, 7...
    "JKLMNPQR",  # zones 2, 5, 8... (no O)
    "STUVWXYZ",  # zones 3, 6, 9...
]
_MGRS_ROW_LETTERS = "ABCDEFGHJKLMNPQRSTUV"  # 20 letters (no I, O)

_GARS_LAT_LETTERS = "ABCDEFGHJKLMNPQRSTUVWXYZ"
_GEOREF_LON_LETTERS = "ABCDEFGHJKLMNPQRSTUVWXYZ"
_GEOREF_LAT_LETTERS = "ABCDEFGHJKLM"
_GEOREF_SUB_LETTERS = "ABCDEFGHJKLMNPQ"

_HEMISPHERES: dict[str, tuple[str, float]] = {
    "N": ("lat", 1.0),
    "NORTH": ("lat", 1.0),
    "S": ("lat", -1.0),
    "SOUTH": ("lat", -1.0),
    "E": ("lon", 1.0),
    "EAST": ("lon", 1.0),
    "W": ("lon", -1.0),
    "WEST": ("lon", -1.0),
}

_DMS_PATTERN = re.compile(
    r"^(?P<deg>\d+(?:\.\d+)?)\s*(?:[°d]|deg(?:rees)?)?"
    r"(?:\s*(?P<min>\d+(?:\.\d+)?)\s*(?:['m′]|min(?:utes)?)?)?"
    r"(?:\s*(?P<sec>\d+(?:\.\d+)?)\s*(?:[\"s″]|sec(?:onds)?)?)?\s*$",
    re.IGNORECASE,
)


@functools.lru_cache(maxsize=128)
def _get_utm_transformer(zone: int, is_south: bool) -> pyproj.Transformer:
    hemi = "+south" if is_south else "+north"
    return pyproj.Transformer.from_crs(
        f"+proj=utm +zone={zone} {hemi} +datum=WGS84", "EPSG:4326", always_xy=True
    )


def _normalize_string(s: str) -> str:
    s = s.strip().strip("\"'").strip("()[]{},; \t\n\r").strip("\"'")
    s = s.replace("′", "'").replace("″", '"')
    s = s.replace("''", '"').replace("\u2019\u2019", '"')
    s = s.replace("\u201c", '"').replace("\u201d", '"')
    s = s.replace("º", "°")
    return s.strip()


def _parse_single_coord(token: str) -> tuple[float, str | None] | None:
    token = _normalize_string(token)
    if not token:
        return None

    direction: str | None = None
    hemi_sign: float = 1.0

    # 1. Hemisphere prefix: e.g. "N37.8", "N 37.8", "North 37.8"
    m_pre = re.match(r"^([NSEW]|North|South|East|West)\s*(.+)$", token, re.IGNORECASE)
    if m_pre:
        hemi_name = m_pre.group(1).upper()
        if hemi_name in _HEMISPHERES:
            direction, hemi_sign = _HEMISPHERES[hemi_name]
            token = m_pre.group(2).strip()

    # 2. Hemisphere suffix: e.g. "37.8 N", "37.8N", "37.8 North"
    if direction is None:
        m_word = re.search(r"\b(North|South|East|West)$", token, re.IGNORECASE)
        if m_word:
            hemi_name = m_word.group(1).upper()
            if hemi_name in _HEMISPHERES:
                direction, hemi_sign = _HEMISPHERES[hemi_name]
                token = token[: m_word.start()].strip()
        else:
            m_suf = re.search(r"([NSEWnsew])$", token)
            if m_suf:
                hemi_char = m_suf.group(1).upper()
                prefix = token[: m_suf.start()].strip()
                # Disambiguate seconds unit 's' from South hemisphere
                is_seconds = False
                if hemi_char == "S" and re.search(r"\d$", prefix):
                    parts = re.split(r"[\s°'\"dms]+", prefix)
                    parts = [p for p in parts if p]
                    if len(parts) >= 2 or re.search(r"['′m]|min|[°d]|deg", prefix, re.IGNORECASE):
                        is_seconds = True

                if not is_seconds and hemi_char in _HEMISPHERES:
                    direction, hemi_sign = _HEMISPHERES[hemi_char]
                    token = prefix

    # 3. Leading sign (+/-)
    sign: float = 1.0
    if token.startswith("-"):
        sign = -1.0
        token = token[1:].strip()
    elif token.startswith("+"):
        sign = 1.0
        token = token[1:].strip()

    # Reject inputs combining an explicit sign with a hemisphere indicator (e.g. "-37.8N").
    # ArcGIS Pro never produces this; accepting it would require guessing precedence.
    if direction is not None and sign != 1.0:
        return None
    final_sign = hemi_sign if direction is not None else sign

    # 4. Handle space-separated or colon-separated DMS/DDM tokens (e.g. "37 49 28.4" or "37:49:28.4")
    token = token.replace(":", " ")
    if " " in token:
        parts = token.split()
        if parts and parts[-1].upper() in _HEMISPHERES:
            if direction is None:
                direction, h_sign = _HEMISPHERES[parts[-1].upper()]
                final_sign = final_sign * h_sign
            parts = parts[:-1]
        try:
            nums = [float(p) for p in parts]
        except ValueError:
            nums = []
        if len(nums) == 1:
            val = nums[0]
        elif len(nums) == 2:
            val = nums[0] + nums[1] / 60.0
        elif len(nums) >= 3:
            val = nums[0] + nums[1] / 60.0 + nums[2] / 3600.0
        else:
            val = None

        if val is not None:
            val = val * final_sign
            return (val, direction) if not (math.isnan(val) or math.isinf(val)) else None

    # 5. Direct decimal conversion
    try:
        val = float(token) * final_sign
        return (val, direction) if not (math.isnan(val) or math.isinf(val)) else None
    except ValueError:
        pass

    # 6. Extract degrees, minutes, seconds using regex
    m = _DMS_PATTERN.match(token)
    if not m:
        return None

    deg_str = m.group("deg")
    min_str = m.group("min")
    sec_str = m.group("sec")

    try:
        deg = float(deg_str)
        minutes = float(min_str) if min_str is not None else 0.0
        seconds = float(sec_str) if sec_str is not None else 0.0
    except (ValueError, TypeError):
        return None

    if min_str is not None and (not deg.is_integer() or not (0.0 <= minutes < 60.0)):
        return None
    if sec_str is not None and (not minutes.is_integer() or not (0.0 <= seconds < 60.0)):
        return None

    val = (deg + (minutes / 60.0) + (seconds / 3600.0)) * final_sign
    if math.isnan(val) or math.isinf(val):
        return None

    return val, direction


def _parse_utm(s: str) -> tuple[float, float] | None:
    s = _normalize_string(s)
    pattern = (
        r"^(?:(?:UTM(?:\s+Zone)?|Zone)\s*:?\s*)?(?P<zone>\d{1,2})\s*(?P<band>[A-Za-z]+)?\s*[,;]?\s*"
        r"(?P<east>\d+(?:\.\d+)?)\s*(?:mE|m)?\s*[,;]?\s*"
        r"(?P<north>\d+(?:\.\d+)?)\s*(?:mN|m)?$"
    )
    m = re.match(pattern, s, re.IGNORECASE)
    if not m:
        return None

    try:
        zone = int(m.group("zone"))
        easting = float(m.group("east"))
        northing = float(m.group("north"))
    except (ValueError, TypeError):
        return None

    if not (1 <= zone <= 60):
        return None

    band = m.group("band").upper() if m.group("band") else None
    is_south = False
    if band:
        # In UTM context, single-letter S/N are hemisphere indicators (ArcGIS Pro convention).
        # Band letters (C-X) are an MGRS concept handled by _parse_mgrs_or_usng.
        if band in ("S", "SOUTH") or (len(band) == 1 and band in "CDEFGHJKLM"):
            is_south = True
        elif band in ("N", "NORTH") or (len(band) == 1 and band in "NPQRTUVWX"):
            is_south = False
        else:
            return None

    try:
        t = _get_utm_transformer(zone, is_south=is_south)
        lon, lat = t.transform(easting, northing)
        if not (-180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0):
            return None
        return float(lon), float(lat)
    except (pyproj.exceptions.ProjError, ValueError, TypeError):
        return None


def _parse_mgrs_or_usng(s: str) -> tuple[float, float] | None:
    s = s.replace(" ", "").upper()
    m = re.match(r"^(\d{1,2})([C-HJ-NP-X])([A-HJ-NP-Z]{2})(\d*)$", s)
    if not m:
        return None

    try:
        zone = int(m.group(1))
    except ValueError:
        return None

    if not (1 <= zone <= 60):
        return None

    band = m.group(2)
    sq = m.group(3)
    digits = m.group(4)
    if len(digits) % 2 != 0:
        return None

    col_char, row_char = sq[0], sq[1]
    col_set = _MGRS_COL_SETS[(zone - 1) % 3]
    if col_char not in col_set or row_char not in _MGRS_ROW_LETTERS:
        return None

    col_idx = col_set.index(col_char)
    easting_100k = (col_idx + 1) * 100000

    row_idx = _MGRS_ROW_LETTERS.index(row_char)
    row_offset = 5 if (zone % 2 == 0) else 0
    northing_100k = ((row_idx - row_offset) % 20) * 100000

    k = len(digits) // 2
    if k > 0:
        mult = 10 ** (5 - k)
        easting = easting_100k + int(digits[:k]) * mult + mult / 2.0
        northing = northing_100k + int(digits[k:]) * mult + mult / 2.0
    else:
        easting = easting_100k + 50000.0
        northing = northing_100k + 50000.0

    band_idx = _BANDS.index(band)
    approx_lat = -80.0 + band_idx * 8.0 + 4.0
    is_south = band_idx < 10

    approx_northing = (approx_lat / 90.0) * 10000000.0
    if is_south:
        approx_northing += 10000000.0

    cycle = round((approx_northing - northing) / 2000000.0)
    northing += cycle * 2000000.0

    try:
        t = _get_utm_transformer(zone, is_south=is_south)
        lon, lat = t.transform(easting, northing)
        if not (-180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0):
            return None
        return float(lon), float(lat)
    except (pyproj.exceptions.ProjError, ValueError, TypeError):
        return None


def _parse_gars(s: str) -> tuple[float, float] | None:
    s = s.replace(" ", "").upper()
    m = re.match(r"^(\d{3})([A-HJ-NP-Z]{2})(?:([1-4])([1-9])?)?$", s)
    if not m:
        return None

    lon_band = int(m.group(1))
    if not (1 <= lon_band <= 720):
        return None

    lat_str = m.group(2)
    if lat_str[0] not in _GARS_LAT_LETTERS or lat_str[1] not in _GARS_LAT_LETTERS:
        return None

    lat_idx = _GARS_LAT_LETTERS.index(lat_str[0]) * 24 + _GARS_LAT_LETTERS.index(lat_str[1])
    if lat_idx >= 360:
        return None

    lon = -180.0 + (lon_band - 1) * 0.5
    lat = -90.0 + lat_idx * 0.5
    cell_size = 0.5

    quadrant = m.group(3)
    if quadrant:
        q = int(quadrant)
        cell_size = 0.25
        if q == 1:
            lat += 0.25
        elif q == 2:
            lon += 0.25
            lat += 0.25
        elif q == 3:
            pass
        elif q == 4:
            lon += 0.25

        keypad = m.group(4)
        if keypad:
            kp = int(keypad)
            cell_size = 5.0 / 60.0
            row = (kp - 1) // 3
            col = (kp - 1) % 3
            lat += (2 - row) * cell_size
            lon += col * cell_size

    lon += cell_size / 2.0
    lat += cell_size / 2.0
    return float(lon), float(lat)


def _parse_georef(s: str) -> tuple[float, float] | None:
    s = s.replace(" ", "").upper()
    m = re.match(r"^([A-HJ-NP-Z][A-HJ-M])([A-HJ-NP-Q]{2})((?:\d{2}){1,4})$", s)
    if not m:
        return None

    q15 = m.group(1)
    q1 = m.group(2)
    digits = m.group(3)

    lon = -180.0 + _GEOREF_LON_LETTERS.index(q15[0]) * 15.0
    lat = -90.0 + _GEOREF_LAT_LETTERS.index(q15[1]) * 15.0

    lon += _GEOREF_SUB_LETTERS.index(q1[0]) * 1.0
    lat += _GEOREF_SUB_LETTERS.index(q1[1]) * 1.0

    k = len(digits) // 2
    scale = 10 ** (k - 2)
    min_lon = int(digits[:k]) / scale
    min_lat = int(digits[k:]) / scale
    lon += (min_lon + 0.5 / scale) / 60.0
    lat += (min_lat + 0.5 / scale) / 60.0

    return float(lon), float(lat)


def _split_coord_string(s: str) -> list[str] | None:
    s = _normalize_string(s)
    if not s:
        return None

    # Case 1: Explicit delimiter (comma, semicolon, slash)
    for delim in (",", ";", "/"):
        if delim in s:
            parts = [p.strip() for p in s.split(delim)]
            if len(parts) == 2 and parts[0] and parts[1]:
                return parts

    # Case 2: Compact unspaced formats with hemisphere prefixes or suffixes
    # Subcase 2a: Hemisphere prefixes: e.g. "N37.824553W122.248383"
    m_pref = re.match(r"^([NSEW][^NSEW]+?)\s*([NSEW].+)$", s, re.IGNORECASE)
    if m_pref:
        return [m_pref.group(1).strip(), m_pref.group(2).strip()]

    # Subcase 2b: Hemisphere suffixes: e.g. "37.824553N122.248383W" or "37°49'28.39"N122°14'54.18"W"
    m_suf = re.match(r"^(.+?[0-9\"'′″°dms][NSEW])\s*([0-9].+[NSEW])$", s, re.IGNORECASE)
    if m_suf:
        return [m_suf.group(1).strip(), m_suf.group(2).strip()]

    # Subcase 2c: Compact signed format: e.g. "+37.824553-122.248383"
    m_sign = re.match(r"^([+-]?[0-9]+(?:\.[0-9]+)?(?:[°d\"'′″]\s*)?)\s*([+-][0-9].+)$", s)
    if m_sign:
        return [m_sign.group(1).strip(), m_sign.group(2).strip()]

    # Case 3: Space-separated tokens
    tokens = s.split()
    clean_tokens = [t.rstrip(",;/") for t in tokens if t.rstrip(",;/")]
    if len(clean_tokens) == 2:
        return clean_tokens

    # Check for two hemisphere markers in tokens
    def is_hemi(tok: str) -> bool:
        return tok.upper() in ("N", "S", "E", "W", "NORTH", "SOUTH", "EAST", "WEST")

    # Tokens with hemisphere prefixes: e.g. ["N", "37°", "49′", "28.39″", "W", "122°", "14′", "54.18″"]
    if clean_tokens and is_hemi(clean_tokens[0]):
        hemi_indices = [i for i, t in enumerate(clean_tokens) if is_hemi(t)]
        if len(hemi_indices) == 2 and hemi_indices[1] > 0:
            idx = hemi_indices[1]
            return [" ".join(clean_tokens[:idx]), " ".join(clean_tokens[idx:])]

    # Tokens with hemisphere suffixes: e.g. ["37", "49", "28.39", "N", "122", "14", "54.18", "W"]
    hemi_suffix_indices = [
        i for i, t in enumerate(clean_tokens) if is_hemi(t) or re.search(r"[0-9][NSEWnsew]$", t)
    ]
    if len(hemi_suffix_indices) == 2:
        split_idx = hemi_suffix_indices[0] + 1
        return [" ".join(clean_tokens[:split_idx]), " ".join(clean_tokens[split_idx:])]

    # Even number of tokens without hemisphere: e.g. DDM (4 tokens), DMS (6 tokens)
    if len(clean_tokens) in (4, 6):
        mid = len(clean_tokens) // 2
        return [" ".join(clean_tokens[:mid]), " ".join(clean_tokens[mid:])]

    return None


def _orient_lon_lat(val1: float, val2: float) -> tuple[float, float]:
    """Guess lon/lat assignment from value ranges: |v| > 90 must be longitude."""
    if abs(val1) > 90 and abs(val2) <= 90:
        return val1, val2
    if abs(val2) > 90 and abs(val1) <= 90:
        return val2, val1
    return val1, val2  # default: (lon, lat) order


def parse_coordinates(*args: Any) -> tuple[float, float] | None:
    """
    Parse a variety of coordinate representations into a (longitude, latitude) tuple.

    Supports all copy/paste formats from Esri ArcGIS Pro:
        - Decimal Degrees (DD): e.g. -122.2483823, 37.8245529 or 37.8245529N 122.2483823W
        - Degrees Decimal Minutes (DDM): e.g. 37° 49.473' N, 122° 14.903' W
        - Degrees Minutes Seconds (DMS): e.g. 37° 49' 28.4" N, 122° 14' 54.2" W
        - Universal Transverse Mercator (UTM): e.g. 10S 566147 4186615 or 10N 566147 4186615
        - Military Grid Reference System (MGRS): e.g. 10SEG6614786615 or 31UDQ4825211932
        - United States National Grid (USNG): e.g. 10S EG 6614 8661
        - Global Area Reference System (GARS): e.g. 006AG39
        - World Geographic Reference System (GEOREF): e.g. MKPG1204
        - Delimited by comma, space, semicolon, or slash
        - Enclosed in parentheses or brackets
        - Unquoted multi-argument shell pastes

    Returns:
        (longitude, latitude) as (float, float), or None if invalid.
    """
    if not args:
        return None

    # Handle single container argument: tuple or list
    if len(args) == 1 and isinstance(args[0], (tuple, list)):
        return parse_coordinates(*args[0])

    # Fast path for direct numeric arguments: (float/int, float/int)
    if len(args) == 2 and isinstance(args[0], (int, float)) and isinstance(args[1], (int, float)):
        lon, lat = _orient_lon_lat(float(args[0]), float(args[1]))
        if -180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0:
            return float(lon), float(lat)
        return None

    joined = " ".join(str(a) for a in args).strip()
    if not joined:
        return None

    # Protect ISO-3166-2 codes (e.g. US-CA, SG-01, GB-LND) from being parsed as coordinates
    if re.fullmatch(r"[A-Za-z]{2}-[A-Za-z0-9]{1,3}", joined):
        return None

    # Single-string grid formats: UTM, MGRS/USNG, GARS, GEOREF
    res_utm = _parse_utm(joined)
    if res_utm is not None:
        return res_utm

    res_mgrs = _parse_mgrs_or_usng(joined)
    if res_mgrs is not None:
        return res_mgrs

    res_gars = _parse_gars(joined)
    if res_gars is not None:
        return res_gars

    res_georef = _parse_georef(joined)
    if res_georef is not None:
        return res_georef

    # Split into coordinate pair
    parts = _split_coord_string(joined)
    if not parts or len(parts) != 2:
        return None

    c1 = _parse_single_coord(parts[0])
    c2 = _parse_single_coord(parts[1])
    if c1 is None or c2 is None:
        return None

    val1, dir1 = c1
    val2, dir2 = c2

    if dir1 == "lon" and dir2 == "lat":
        lon, lat = val1, val2
    elif dir1 == "lat" and dir2 == "lon":
        lon, lat = val2, val1
    elif dir1 and dir2 and dir1 == dir2:
        return None
    elif dir1 == "lat" and dir2 is None:
        lon, lat = val2, val1
    elif (dir1 == "lon" and dir2 is None) or (dir1 is None and dir2 == "lat"):
        lon, lat = val1, val2
    elif dir1 is None and dir2 == "lon":
        lon, lat = val2, val1
    else:
        # Both directions unspecified: check range exclusivity
        lon, lat = _orient_lon_lat(val1, val2)

    if not (-180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0):
        return None

    if math.isnan(lon) or math.isnan(lat) or math.isinf(lon) or math.isinf(lat):
        return None

    return float(lon), float(lat)

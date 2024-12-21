import folium
import json
import pandas as pd
import math
from folium.plugins import Search
import matplotlib.pyplot as plt
from matplotlib.colors import to_hex

def generate_distinct_colors(n):
    cmaps = [plt.get_cmap('tab20'), plt.get_cmap('tab20b'), plt.get_cmap('tab20c')]
    colors = []
    for cm in cmaps:
        for i in range(cm.N):
            colors.append(to_hex(cm(i)))
    return colors[:n]

def safe_str(value):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return str(value).strip()

# File paths (Adjust as needed)
all_polygon_file = "./data/geojson/All_Zip_Polygons.geojson"
all_point_file = "./data/geojson/All_Zip_Points.geojson"

base_excel_file = "./data/excel/New_ZipCode_NoDuplicates.xlsx"
# Now using CSV for chapter data:
chapter_csv_file = "./data/excel/CHAPTERMEMBERS_Updated_CSV.csv"

# Read base data as Excel (unchanged):
df_base = pd.read_excel(base_excel_file, dtype=str)
# Read chapter data as CSV:
df_chapter = pd.read_csv(chapter_csv_file, dtype=str)

with open(all_polygon_file, 'r') as f:
    polygons_data = json.load(f)

with open(all_point_file, 'r') as f:
    points_data = json.load(f)

# Index polygons by ZCTA5CE20
polygon_index = {}
for feat in polygons_data["features"]:
    zcta = safe_str(feat["properties"].get("ZCTA5CE20", ""))
    polygon_index[zcta] = feat

# Index points by ZIP_CODE
point_index = {}
for feat in points_data["features"]:
    zip_code_pt = safe_str(feat["properties"].get("ZIP_CODE", ""))
    point_index[zip_code_pt] = feat

def zero_pad_zip(z):
    return str(z).zfill(5)

def get_zip_list_from_range(zip_range_str):
    start_str, end_str = zip_range_str.split('-')
    start_int = int(start_str)
    end_int = int(end_str)
    return [zero_pad_zip(i) for i in range(start_int, end_int+1)]

########################################
# PROCESS BASE ZIP RANGES
########################################

base_polygons = []
base_points = []

for _, row in df_base.iterrows():
    zip_range = safe_str(row.get("Zip_Code_Range", ""))
    if not zip_range:
        continue
    chapter = safe_str(row.get("Chapter", ""))
    state_prov = safe_str(row.get("State_Province", ""))
    x_ref_type = safe_str(row.get("X_Ref_Type", ""))

    zip_codes = get_zip_list_from_range(zip_range)
    for zc in zip_codes:
        if zc in polygon_index:
            feat = polygon_index[zc]
            feat_copy = json.loads(json.dumps(feat))
            feat_copy["properties"]["Chapter"] = chapter
            feat_copy["properties"]["State_Province"] = state_prov
            feat_copy["properties"]["X_Ref_Type"] = x_ref_type
            feat_copy["properties"]["Type"] = "Base Boundary"
            base_polygons.append(feat_copy)
        else:
            if zc in point_index:
                feat = point_index[zc]
                feat_copy = json.loads(json.dumps(feat))
                # Keep only ZIP_CODE
                original_zip = safe_str(feat_copy["properties"].get("ZIP_CODE", ""))
                feat_copy["properties"] = {}
                feat_copy["properties"]["ZIP_CODE"] = original_zip
                feat_copy["properties"]["Chapter"] = chapter
                feat_copy["properties"]["State_Province"] = state_prov
                feat_copy["properties"]["X_Ref_Type"] = x_ref_type
                feat_copy["properties"]["Type"] = "Base Point"
                base_points.append(feat_copy)

########################################
# PROCESS CHAPTER MEMBER ZIP CODES - AGGREGATED
########################################

chapter_zip_dict = {}
for _, row in df_chapter.iterrows():
    zip_code = safe_str(row.get("Zip_Code", ""))
    if zip_code:
        chapter_zip_dict.setdefault(zip_code, []).append(row)

chapter_polygons = []
chapter_points = []

for zc, rows_for_zip in chapter_zip_dict.items():
    if zc in polygon_index:
        feat = polygon_index[zc]
        feat_copy = json.loads(json.dumps(feat))
        feat_copy["properties"]["Type"] = "Chapter Boundary"

        html_parts = []
        for i, row_data in enumerate(rows_for_zip):
            ptype = safe_str(row_data.get("Primary Business Type", ""))
            benefit = safe_str(row_data.get("Benefit", ""))
            city = safe_str(row_data.get("City", ""))
            state_prov = safe_str(row_data.get("State/Province", ""))
            zip_postal = safe_str(row_data.get("ZIP/Postal Code", ""))
            chapter_territory = safe_str(row_data.get("Chapter Territory", ""))

            part_html = (f"<b>Zip_Code:</b> {zc}<br>"
                         f"<b>Primary Business Type:</b> {ptype}<br>"
                         f"<b>Benefit:</b> {benefit}<br>"
                         f"<b>City:</b> {city}<br>"
                         f"<b>State/Province:</b> {state_prov}<br>"
                         f"<b>ZIP/Postal Code:</b> {zip_postal}<br>"
                         f"<b>Chapter Territory:</b> {chapter_territory}<br>")
            if i > 0:
                html_parts.append("<hr>")
            html_parts.append(part_html)

        combined_html = "<div style='max-height:300px; overflow:auto;'>" + "".join(html_parts) + "</div>"
        feat_copy["properties"]["excel_info_html"] = combined_html
        feat_copy["properties"]["Chapter Territory"] = safe_str(rows_for_zip[0].get("Chapter Territory", ""))

        chapter_polygons.append(feat_copy)

    elif zc in point_index:
        feat = point_index[zc]
        feat_copy = json.loads(json.dumps(feat))
        feat_copy["properties"]["Type"] = "Chapter Point"

        # Keep only ZIP_CODE
        original_zip = safe_str(feat_copy["properties"].get("ZIP_CODE", ""))
        feat_copy["properties"] = {}
        feat_copy["properties"]["ZIP_CODE"] = original_zip
        feat_copy["properties"]["Type"] = "Chapter Point"

        html_parts = []
        for i, row_data in enumerate(rows_for_zip):
            ptype = safe_str(row_data.get("Primary Business Type", ""))
            benefit = safe_str(row_data.get("Benefit", ""))
            city = safe_str(row_data.get("City", ""))
            state_prov = safe_str(row_data.get("State/Province", ""))
            zip_postal = safe_str(row_data.get("ZIP/Postal Code", ""))
            chapter_territory = safe_str(row_data.get("Chapter Territory", ""))

            part_html = (f"<b>Zip_Code:</b> {zc}<br>"
                         f"<b>Primary Business Type:</b> {ptype}<br>"
                         f"<b>Benefit:</b> {benefit}<br>"
                         f"<b>City:</b> {city}<br>"
                         f"<b>State/Province:</b> {state_prov}<br>"
                         f"<b>ZIP/Postal Code:</b> {zip_postal}<br>"
                         f"<b>Chapter Territory:</b> {chapter_territory}<br>")
            if i > 0:
                html_parts.append("<hr>")
            html_parts.append(part_html)

        combined_html = "<div style='max-height:300px; overflow:auto;'>" + "".join(html_parts) + "</div>"
        feat_copy["properties"]["excel_info_html"] = combined_html
        feat_copy["properties"]["Chapter Territory"] = safe_str(rows_for_zip[0].get("Chapter Territory", ""))

        chapter_points.append(feat_copy)

########################################
# CREATE MAP
########################################

m = folium.Map(location=[39.8283, -98.5795], zoom_start=5, tiles="cartodbpositron")

chapter_territories_set = set()
for feat in chapter_polygons + chapter_points:
    val = feat["properties"].get("Chapter Territory", "")
    t = safe_str(val)
    if t:
        chapter_territories_set.add(t)

base_chapters_set = set()
for feat in base_polygons + base_points:
    c = safe_str(feat["properties"].get("Chapter", ""))
    if c:
        base_chapters_set.add(c)

all_territories = list(chapter_territories_set.union(base_chapters_set))
color_list = generate_distinct_colors(len(all_territories))
territory_color_map = {}
for i, territory in enumerate(sorted(all_territories)):
    territory_color_map[territory] = color_list[i]

def base_boundaries_style(feature):
    return {
        "fillColor": "#9C9C9C",
        "color": "#9C9C9C",
        "weight": 0.5,
        "fillOpacity": 0.4
    }

def chapter_boundaries_style(feature):
    territory = safe_str(feature["properties"].get("Chapter Territory", ""))
    color = territory_color_map.get(territory, "#FFEBAF")
    return {
        "fillColor": color,
        "color": "#696969",
        "weight": 0.5,
        "fillOpacity": 0.7,
    }

def base_points_style(feature):
    return "#9C9C9C", "#828282"

def chapter_points_style(feature):
    territory = safe_str(feature["properties"].get("Chapter Territory", ""))
    color = territory_color_map.get(territory, "#FF9BDA")
    return color, color

# Add layers in order:
# Base polygons
if base_polygons:
    base_polygon_layer = folium.GeoJson(
        {"type": "FeatureCollection", "features": base_polygons},
        name="Base Zip Boundaries",
        style_function=base_boundaries_style,
        highlight_function=lambda x: {"weight": 2, "color": "#FF6F61", "fillOpacity": 0.7},
        tooltip=folium.GeoJsonTooltip(
            fields=["ZCTA5CE20","Chapter","State_Province","X_Ref_Type"],
            aliases=["<b>Zip_Code:</b>", "<b>Chapter:</b>", "<b>State_Province:</b>", "<b>X_Ref_Type:</b>"],
            localize=True
        )
    ).add_to(m)
else:
    base_polygon_layer = None

# Chapter polygons
if chapter_polygons:
    chapter_boundaries_layer = folium.GeoJson(
        {"type": "FeatureCollection", "features": chapter_polygons},
        name="Chapter Member Boundaries",
        style_function=chapter_boundaries_style,
        highlight_function=lambda x: {"weight": 2, "color": "#FF6F61", "fillOpacity": 0.7},
        popup=folium.GeoJsonPopup(
            fields=["excel_info_html"],
            aliases=[""],
            labels=False,
            parse_html=True
        )
    ).add_to(m)
else:
    chapter_boundaries_layer = None

# Base points
if base_points:
    base_points_group = folium.FeatureGroup(name="Base Zip Points", show=True)
    for feat in base_points:
        coords = feat["geometry"]["coordinates"]
        props = feat["properties"]
        tooltip_str = (
            f"<b>ZIP_CODE:</b> {props.get('ZIP_CODE','')}<br>"
            f"<b>Chapter:</b> {props.get('Chapter','')}<br>"
            f"<b>State_Province:</b> {props.get('State_Province','')}<br>"
            f"<b>X_Ref_Type:</b> {props.get('X_Ref_Type','')}"
        )
        fill_color, line_color = base_points_style(feat)
        folium.CircleMarker(
            location=[coords[1], coords[0]],
            radius=4,
            fill=True,
            fill_color=fill_color,
            color=line_color,
            fill_opacity=0.9,
            tooltip=tooltip_str
        ).add_to(base_points_group)
    base_points_group.add_to(m)

# Chapter points
if chapter_points:
    chapter_points_group = folium.FeatureGroup(name="Chapter Member Points", show=True)
    for feat in chapter_points:
        coords = feat["geometry"]["coordinates"]
        props = feat["properties"]
        fill_color, line_color = chapter_points_style(feat)
        popup_html = props.get("excel_info_html", "No data")
        tooltip_str = (
            f"<b>ZIP_CODE:</b> {props.get('ZIP_CODE','')}<br>"
            f"<b>Chapter Territory:</b> {props.get('Chapter Territory','')}<br>"
        )
        folium.CircleMarker(
            location=[coords[1], coords[0]],
            radius=4,
            fill=True,
            fill_color=fill_color,
            color=line_color,
            fill_opacity=0.9,
            tooltip=tooltip_str,
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(chapter_points_group)
    chapter_points_group.add_to(m)

# Add search if chapter_boundaries_layer exists
if chapter_boundaries_layer:
    Search(
        layer=chapter_boundaries_layer,
        search_label='ZCTA5CE20',
        placeholder='Search by Zip Code',
        collapsed=False,
        search_zoom=10
    ).add_to(m)

# Legend
legend_html = f'''
<div style="
    position: fixed; 
    top:125px; 
    left:10px; 
    max-height:80vh; 
    overflow:auto; 
    background-color:rgba(255,255,255,0.7); 
    padding:10px; 
    border:2px solid grey; 
    font-size:14px; 
    z-index:9999;
">
<b>Legend (Territories/Chapters)</b><br>
'''
for territory, color in territory_color_map.items():
    legend_html += f'<i style="background:{color};width:10px;height:10px;display:inline-block;margin-right:5px;"></i>{territory}<br>'
legend_html += '</div>'
legend = folium.Element(legend_html)
m.get_root().html.add_child(legend)

folium.LayerControl().add_to(m)

############################################
# Add a toggle button + dropdown (hidden by default)
############################################

chapter_filter_html = '''
<div id="chapter-filter-toggle" style="
    position: fixed; 
    top:165px; 
    right:10px; 
    background-color:rgba(255,255,255,0.9); 
    padding:5px; 
    border:2px solid grey; 
    font-size:14px; 
    cursor:pointer; 
    z-index:9999;
">
<b>Filter Chapter Territories</b>
</div>

<div id="chapter-filter-container" style="
    position: fixed; 
    top:200px; 
    right:10px; 
    max-height:70vh; 
    overflow:auto; 
    background-color:rgba(255,255,255,0.9); 
    padding:10px; 
    border:2px solid grey; 
    font-size:14px; 
    z-index:9999;
    display:none;
">
<input type="checkbox" id="all-chapters" checked> All Chapters<br>
<div id="chapter-checkboxes" style="margin-left:20px;">
'''

for territory in sorted(chapter_territories_set):
    chapter_filter_html += f'<label><input type="checkbox" class="chapter-checkbox" value="{territory}" checked> {territory}</label><br>'

chapter_filter_html += '''
</div>
<button id="apply-filter" style="margin-top:5px;">Apply</button>
</div>
'''

chapter_filter_element = folium.Element(chapter_filter_html)
m.get_root().html.add_child(chapter_filter_element)

js_script = """
<script>
function updateLegendVisibleChapters(selectedChapters) {
    var legendItems = document.querySelectorAll('#legend-container .legend-item');
    legendItems.forEach(function(item) {
        var t = item.getAttribute('data-territory');
        if (selectedChapters.includes(t)) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    var allChaptersCheckbox = document.getElementById('all-chapters');
    var chapterCheckboxes = document.querySelectorAll('.chapter-checkbox');
    var filterContainer = document.getElementById('chapter-filter-container');
    var filterToggle = document.getElementById('chapter-filter-toggle');

    // Toggle the dropdown panel
    filterToggle.addEventListener('click', function() {
        if (filterContainer.style.display === 'none') {
            filterContainer.style.display = 'block';
        } else {
            filterContainer.style.display = 'none';
        }
    });

    allChaptersCheckbox.addEventListener('change', function() {
        if (allChaptersCheckbox.checked) {
            chapterCheckboxes.forEach(function(cb) {
                cb.checked = true;
            });
        } else {
            chapterCheckboxes.forEach(function(cb) {
                cb.checked = false;
            });
        }
    });

    chapterCheckboxes.forEach(function(cb) {
        cb.addEventListener('change', function() {
            if (!cb.checked) {
                allChaptersCheckbox.checked = false;
            } else {
                var allChecked = true;
                chapterCheckboxes.forEach(function(c) {
                    if (!c.checked) allChecked = false;
                });
                allChaptersCheckbox.checked = allChecked;
            }
        });
    });

    document.getElementById('apply-filter').addEventListener('click', function() {
        var selectedChapters = [];
        chapterCheckboxes.forEach(function(cb) {
            if (cb.checked) {
                selectedChapters.push(cb.value);
            }
        });
        if (allChaptersCheckbox.checked) {
            showHideFeatures(true, []);
            updateLegendVisibleChapters(Array.from(chapterCheckboxes).map(function(c){return c.value;}));
        } else {
            showHideFeatures(false, selectedChapters);
            updateLegendVisibleChapters(selectedChapters);
        }
    });

    function showHideFeatures(showAll, allowedChapters) {
        var map = window.map_""" + m._id + """;
        map.eachLayer(function(layer) {
            function applyDisplayToFeature(featureLayer) {
                if (featureLayer.feature && featureLayer.feature.properties) {
                    var props = featureLayer.feature.properties;
                    var fType = props.Type;
                    var feat_territory = '';
                    if (props['Chapter Territory']) {
                        feat_territory = props['Chapter Territory'].trim();
                    }
                    if (fType === 'Chapter Boundary' || fType === 'Chapter Point') {
                        var visible = showAll || allowedChapters.includes(feat_territory);
                        if (featureLayer.setStyle && featureLayer.feature.geometry && featureLayer.feature.geometry.type !== 'Point') {
                            if (featureLayer._path) {
                                featureLayer._path.style.display = visible ? 'block' : 'none';
                            }
                            if (visible) {
                                featureLayer.setStyle({opacity:1, fillOpacity:0.7});
                            }
                        }
                        if (featureLayer._icon) {
                            featureLayer._icon.style.display = visible ? 'block' : 'none';
                        }
                        if (featureLayer._path && featureLayer.feature.geometry && featureLayer.feature.geometry.type === 'Point') {
                            featureLayer._path.style.display = visible ? 'block' : 'none';
                        }
                    }
                }
            }

            if (layer instanceof L.GeoJSON || layer instanceof L.FeatureGroup) {
                if (layer._layers) {
                    for (var key in layer._layers) {
                        if (layer._layers.hasOwnProperty(key)) {
                            var subLayer = layer._layers[key];
                            applyDisplayToFeature(subLayer);
                        }
                    }
                }
            } else {
                applyDisplayToFeature(layer);
            }
        });
    }

    // Initially, all chapters are selected
    updateLegendVisibleChapters(Array.from(chapterCheckboxes).map(function(c){return c.value;}));
});
</script>
"""

script_element = folium.Element(js_script)
m.get_root().html.add_child(script_element)

m.save("index.html")
print("Map has been created and saved as 'index.html'.")

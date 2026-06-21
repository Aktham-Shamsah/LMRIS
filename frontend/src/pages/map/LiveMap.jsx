import { useEffect, useMemo, useState } from "react";
import { GeoJSON, MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import L from "leaflet";
import Panel from "../../components/Panel";
import Message from "../../components/Message";
import { parcelGeofeed, pendingHeatmap } from "../../api/analytics";

const markerIcon = L.divIcon({
  className: "pending-marker",
  html: "<span style='display:block;width:14px;height:14px;border-radius:50%;background:#a12828;border:2px solid white'></span>",
  iconSize: [18, 18]
});

function firstCoordinate(geometry) {
  if (!geometry) return null;
  if (geometry.type === "Point") return geometry.coordinates;
  const ring = geometry.coordinates?.[0]?.[0] ? geometry.coordinates[0] : geometry.coordinates;
  return ring?.[0] || null;
}

export default function LiveMap() {
  const [filters, setFilters] = useState({ zone_id: "", status: "", application_type: "", dispute_state: "" });
  const [parcels, setParcels] = useState({ type: "FeatureCollection", features: [] });
  const [pending, setPending] = useState({ type: "FeatureCollection", features: [] });
  const [error, setError] = useState("");

  async function load() {
    try {
      setError("");
      const [parcelData, pendingData] = await Promise.all([parcelGeofeed(filters), pendingHeatmap()]);
      setParcels(parcelData);
      setPending(pendingData);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const markers = useMemo(() => (pending.features || []).map((feature) => ({ feature, coordinate: firstCoordinate(feature.geometry) })).filter((item) => item.coordinate), [pending]);
  const change = (event) => setFilters({ ...filters, [event.target.name]: event.target.value });

  return (
    <Panel title="Live Parcel Map" actions={<button onClick={load}>Apply Filters</button>}>
      <div className="form-grid">
        <label>Zone
          <input name="zone_id" value={filters.zone_id} onChange={change} placeholder="ZONE-RM-01" />
        </label>
        <label>Status
          <input name="status" value={filters.status} onChange={change} placeholder="survey_required" />
        </label>
        <label>Type
          <input name="application_type" value={filters.application_type} onChange={change} placeholder="boundary_correction" />
        </label>
        <label>Dispute
          <select name="dispute_state" value={filters.dispute_state} onChange={change}>
            <option value="">All</option>
            <option value="none">none</option>
            <option value="under_objection">under_objection</option>
          </select>
        </label>
      </div>
      <Message error={error} />
      <div className="map">
        <MapContainer center={[31.9035, 35.203]} zoom={14} scrollWheelZoom>
          <TileLayer attribution="&copy; OpenStreetMap contributors" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          <GeoJSON data={parcels} key={JSON.stringify(parcels).length} style={(feature) => ({
            color: feature?.properties?.dispute_state === "under_objection" ? "#a12828" : "#0f6b5f",
            weight: 2,
            fillOpacity: 0.18
          })} />
          {markers.map(({ feature, coordinate }) => (
            <Marker key={`${feature.properties.application_id}-${coordinate.join(",")}`} position={[coordinate[1], coordinate[0]]} icon={markerIcon}>
              <Popup>
                {feature.properties.application_id}<br />
                {feature.properties.status}
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </Panel>
  );
}


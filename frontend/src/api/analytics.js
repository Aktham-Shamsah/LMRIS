import { request } from "./client";

export const getKpis = () => request("/analytics/kpis");
export const applicationsByStatus = () => request("/analytics/applications-by-status");
export const applicationsByZone = () => request("/analytics/applications-by-zone");
export const processingTime = () => request("/analytics/processing-time");
export const surveyorAnalytics = () => request("/analytics/surveyors");
export const registrarAnalytics = () => request("/analytics/registrars");
export const parcelGeofeed = (params = {}) => {
  const query = new URLSearchParams(Object.entries(params).filter(([, value]) => value));
  return request(`/analytics/geofeeds/parcels?${query.toString()}`);
};
export const pendingHeatmap = () => request("/analytics/geofeeds/pending-heatmap");


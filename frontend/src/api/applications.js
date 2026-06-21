import { request } from "./client";

export const listApplications = (params = {}) => {
  const query = new URLSearchParams(Object.entries(params).filter(([, value]) => value !== undefined && value !== ""));
  return request(`/applications/?${query.toString()}`);
};

export const getApplication = (applicationId) => request(`/applications/${applicationId}`);

export const createApplication = (payload, idempotencyKey) =>
  request("/applications/", {
    method: "POST",
    headers: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {},
    body: payload
  });

export const transitionApplication = (applicationId, payload) =>
  request(`/applications/${applicationId}/transition`, { method: "PATCH", body: payload });

export const holdApplication = (applicationId, payload) =>
  request(`/applications/${applicationId}/hold`, { method: "POST", body: payload });

export const rejectApplication = (applicationId, payload) =>
  request(`/applications/${applicationId}/reject`, { method: "POST", body: payload });

export const issueCertificate = (applicationId) =>
  request(`/applications/${applicationId}/certificate`, { method: "POST" });

export const addDocument = (applicationId, payload) =>
  request(`/applications/${applicationId}/documents`, { method: "POST", body: payload });

export const addComment = (applicationId, payload) =>
  request(`/applications/${applicationId}/comments`, { method: "POST", body: payload });

export const addObjection = (applicationId, payload) =>
  request(`/applications/${applicationId}/objections`, { method: "POST", body: payload });

export const getTimeline = (applicationId) => request(`/applications/${applicationId}/timeline`);


import { request } from "./client";

export const createApplicant = (payload) => request("/applicants/", { method: "POST", body: payload });
export const getApplicant = (applicantId) => request(`/applicants/${applicantId}`);
export const getApplicantApplications = (applicantId) => request(`/applicants/${applicantId}/applications`);


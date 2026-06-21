import { request } from "./client";

export const registrarReview = (applicationId, payload) =>
  request(`/applications/${applicationId}/registrar-review`, { method: "PATCH", body: payload });


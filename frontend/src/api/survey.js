import { request } from "./client";

export const listSurveyTasks = (surveyorId = "") => request(`/survey/tasks${surveyorId ? `?surveyor_id=${surveyorId}` : ""}`);
export const autoAssignSurveyor = (applicationId) => request(`/applications/${applicationId}/auto-assign-surveyor`, { method: "POST" });
export const addSurveyMilestone = (applicationId, payload) =>
  request(`/applications/${applicationId}/survey-milestone`, { method: "PATCH", body: payload });
export const uploadSurveyReport = (applicationId, payload) =>
  request(`/applications/${applicationId}/survey-report`, { method: "POST", body: payload });


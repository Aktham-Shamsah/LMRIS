import { request } from "./client";

export const adminApplicants = () => request("/admin/applicants");
export const adminApplications = () => request("/admin/applications");
export const adminStaff = () => request("/admin/staff");
export const adminSystemEvents = () => request("/admin/system-events");
export const adminNotificationEvents = () => request("/admin/notification-events");
export const adminNotificationMessages = () => request("/admin/notification-messages");
export const testEmail = (to) => request("/admin/test-email", { method: "POST", body: { to } });
export const seedDemo = () => request("/admin/seed-demo", { method: "POST" });
export const resetDemo = () => request("/admin/reset-demo", { method: "POST" });

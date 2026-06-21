import { request } from "./client";

export const getCertificate = (certificateId) => request(`/certificates/${certificateId}`);
export const getApplicationCertificate = (applicationId) => request(`/certificates/application/${applicationId}/latest`);


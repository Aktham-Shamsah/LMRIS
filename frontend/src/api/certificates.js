import { API_BASE, request } from "./client";

export const getCertificate = (certificateId) => request(`/certificates/${certificateId}`);
export const getApplicationCertificate = (applicationId) => request(`/certificates/application/${applicationId}/latest`);
export const downloadCertificatePdf = async (certificateId) => {
  const headers = new Headers();
  const token = localStorage.getItem("lrmisToken");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_BASE}/certificates/${certificateId}/pdf`, { headers });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.message || payload.detail || "Could not download certificate PDF");
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  window.open(url, "_blank", "noopener,noreferrer");
  setTimeout(() => URL.revokeObjectURL(url), 30000);
};


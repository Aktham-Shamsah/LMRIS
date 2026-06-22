import { request } from "./client";

export const login = (email, password) => request("/auth/login", { method: "POST", body: { email, password } });
export const me = () => request("/auth/me");
export const signup = (payload) => request("/auth/signup", { method: "POST", body: payload });
export const verifyEmail = (email, otpCode) => request("/auth/verify-email", { method: "POST", body: { email, otp_code: otpCode } });
export const resendOtp = (email) => request("/auth/resend-otp", { method: "POST", body: { email } });


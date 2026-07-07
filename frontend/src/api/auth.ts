import { apiClient } from "./client";
import type { User } from "../types";

export interface LoginPayload {
  email: string;
  password: string;
  otp_token?: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

export async function login(payload: LoginPayload): Promise<LoginResponse> {
  const { data } = await apiClient.post<LoginResponse>("/auth/login/", payload);
  return data;
}

export async function logout(refresh: string): Promise<void> {
  await apiClient.post("/auth/logout/", { refresh });
}

export async function fetchMe(): Promise<User> {
  const { data } = await apiClient.get<User>("/auth/me/");
  return data;
}

export async function updateMe(payload: Partial<User>): Promise<User> {
  const { data } = await apiClient.patch<User>("/auth/me/", payload);
  return data;
}

export async function changePassword(old_password: string, new_password: string) {
  const { data } = await apiClient.post("/auth/change-password/", { old_password, new_password });
  return data;
}

export async function setup2FA() {
  const { data } = await apiClient.post<{ qr_code: string; secret: string }>("/auth/2fa/setup/");
  return data;
}

export async function verify2FA(token: string) {
  const { data } = await apiClient.post("/auth/2fa/verify/", { token });
  return data;
}

export async function disable2FA() {
  const { data } = await apiClient.post("/auth/2fa/disable/");
  return data;
}

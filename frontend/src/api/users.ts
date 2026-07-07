import { createResourceApi } from "./resource";
import type { User } from "../types";

export const usersApi = createResourceApi<User>("/auth/users");

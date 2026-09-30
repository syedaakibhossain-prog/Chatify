import { api } from "./client";


export interface UserSearchResult {
  id: string;
  username: string;
  last_seen: string;
}

/** GET /user/search?username={username} → UserSearchResult */
export const usersApi = {
  search: (username: string) =>
    api.get<UserSearchResult>(`user/search?username=${encodeURIComponent(username)}`),
};

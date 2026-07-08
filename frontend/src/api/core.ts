import { createResourceApi } from "./resource";

export interface PublicHoliday {
  id: number;
  name: string;
  date: string;
  is_recurring_annually: boolean;
  description: string;
  branch: number | null;
}

export const publicHolidaysApi = createResourceApi<PublicHoliday>("/core/public-holidays");

// src/app.d.ts
import type { User, Solution, Company } from '$lib/common/types/platform';

declare global {
  namespace App {
    interface Locals {
      user: User | null;
    }

    interface PageData {
      user: User | null;
      companies?: Company[];
      solutions?: Solution[];
    }
  }
}

export {};

// src/routes/clinic-agent/+layout.server.ts
// Author: Claude
// Created Date: 2026-03-12

import { redirect } from '@sveltejs/kit';
import type { LayoutServerLoad } from './$types';
import { env } from '$env/dynamic/private';

const BACKEND_REDIRECT_URL = env.BACKEND_REDIRECT_URL;

export const load: LayoutServerLoad = async ({ locals, url }) => {
  const user = locals.user;
  const isRootPage = url.pathname === '/clinic-agent';

  // Public landing page — allow anyone
  if (isRootPage) {
    if (user) {
      throw redirect(302, '/clinic-agent/chat');
    }
    return;
  }

  // Sub-pages require login
  if (!user) {
    throw redirect(302, `${BACKEND_REDIRECT_URL}/auth/login?redirect=clinic-agent/setup`);
  }

  // Logged in with a non-clinic-demo company — not allowed
  if (user.company_id && !user.company_name?.startsWith('ClinicDemo-')) {
    throw redirect(302, '/');
  }

  // Already set up — skip straight to chat
  if (user.company_id && url.pathname.startsWith('/clinic-agent/setup')) {
    throw redirect(302, '/clinic-agent/chat');
  }

  // Logged-in without a company — must complete setup first
  if (!user.company_id && !url.pathname.startsWith('/clinic-agent/setup')) {
    throw redirect(302, '/clinic-agent/setup');
  }
};

// src/routes/clinic-agent/setup/+page.server.ts
// Author: Claude
// Created Date: 2026-03-12

import type { Actions } from './$types';
import { fail, redirect } from '@sveltejs/kit';
import { backendApi } from '$lib/common/server/api/client';

export const actions: Actions = {
  default: async (event) => {
    const fd = await event.request.formData();
    const name = (fd.get('name') as string)?.trim();

    if (!name) return fail(400, { message: 'Name is required.' });

    const res = await backendApi.post(event, '/solutions/clinic-agent/setup', { name });

    if (!res.success) {
      return fail(res.error.status, {
        message: res.error.status === 409
          ? 'Demo account limit reached. Thanks for your interest!'
          : 'Something went wrong. Please try again.'
      });
    }

    throw redirect(303, '/clinic-agent/chat');
  }
};

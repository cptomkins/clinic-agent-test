<!-- src/routes/clinic-agent/+page.svelte -->
<!-- Author: Claude -->
<!-- Created Date: 2026-03-12 -->
<!-- Updated: 2026-03-15 — v0.13.1: updated copy for product support agent -->

<script lang="ts">
  import Button from '$lib/common/components/ui/Button.svelte';
  const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;
</script>

<section class="page-bg min-h-screen">
  <div class="mx-auto max-w-2xl px-6 py-10 pt-36 space-y-8 text-center">
    <header>
      <h1 class="page-header">Clinic Agent</h1>
      <p class="mt-3 text-medium font-medium text-subtle">
        An AI-powered support agent for ClinicSoft practice management software.
        Get help with software features, billing questions, troubleshooting,
        and plan upgrades — all in a single conversation.
      </p>
    </header>

    <Button
      variant="primary"
      onClick={() => window.location.href = `${BACKEND_URL}/auth/login?redirect=clinic-agent/chat`}
    >
      Try the Demo
    </Button>
  </div>
</section>

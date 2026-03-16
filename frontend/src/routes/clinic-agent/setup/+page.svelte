<!-- src/routes/clinic-agent/setup/+page.svelte -->
<!-- Author: Claude -->
<!-- Created Date: 2026-03-12 -->
<script lang="ts">
  import { enhance } from '$app/forms';
  import { browser } from '$app/environment';
  import Button from '$lib/common/components/ui/Button.svelte';
  import './setup.css';
  const { form } = $props();
  let loading = $state(false);

  if (browser) {
    localStorage.removeItem('post_login_redirect');
  }
</script>
<section class="page-bg min-h-screen">
  <div class="mx-auto max-w-md px-6 py-10 pt-32 space-y-10">
    <header class="text-center">
      <h1 class="page-header">Set up your demo</h1>
      <p class="mt-2 text-base text-subtle">
        We'll create a sample dental practice with staff, patients, and appointments for you to explore.
      </p>
    </header>
    <form
      method="POST"
      use:enhance={() => {
        loading = true;
        return async ({ update }) => {
          loading = false;
          await update();
        };
      }}
    >
      <div>
        <label class="block text-center text-2xl font-semibold mb-3" for="name">Your name</label>
        <input
          id="name"
          name="name"
          class="input-field"
          placeholder="Jane Doe"
          required
        />
      </div>
      {#if form?.message}
        <p class="text-sm text-subtle mt-3">{form.message}</p>
      {/if}
      <div class="mt-8 setup-btn-wrap">
        <Button variant="primary" type="submit" {loading}>
          {#if loading}
            Setting up…
          {:else}
            Start Demo
          {/if}
        </Button>
      </div>
      <p class="mt-3 text-center text-xs text-subtle">
        By clicking "Start Demo," you agree to receive emails from Harbor Automation.
      </p>
    </form>
  </div>
</section>

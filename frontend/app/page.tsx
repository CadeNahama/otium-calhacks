import { redirect } from 'next/navigation';

export default async function Home() {
  // Auto-redirect to dashboard (local demo - no auth needed)
  redirect('/dashboard');
}

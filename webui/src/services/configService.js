export async function loadSystemConfig() {
  const response = await fetch('/system_config.json');
  if (!response.ok) {
    throw new Error('Failed to load system configuration');
  }
  return response.json();
}

import fetch from "node-fetch";
async function check() {
  try {
    const res = await fetch("https://ais-dev-lgwv2qzzlj6aqwt73tib6i-487719356843.us-east1.run.app/api/health", {
      headers: { 'Accept': 'application/json' }
    });
    console.log("STATUS", res.status);
  } catch (e) {
    console.log("ERROR", e);
  }
}
check();

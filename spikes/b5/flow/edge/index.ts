import { WorkerEntrypoint } from "cloudflare:workers";

export default class extends WorkerEntrypoint {
  async fetch(request: Request): Promise<Response> {
    return new Response("ciao dal bordo");
  }
}

import { getAllAnswers } from "./solver";
import type { WorkerRequest, WorkerResponse } from "./types";

self.onmessage = (event: MessageEvent<WorkerRequest>) => {
  const { remainingWords, validGuesses } = event.data;
  const possibilities = getAllAnswers(remainingWords, validGuesses);
  const response: WorkerResponse = { possibilities };
  self.postMessage(response);
};

"use client";

import { useEffect, useMemo, useState } from "react";

const API_URL = "http://127.0.0.1:8000";

type Detection = {
  class_id: number;
  class_name: string;
  confidence: number;
  bounding_box: {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
  };
};

type JobResult = {
  job_id: string;
  status: string;
  filename: string;
  detections?: Detection[];
  detection_count?: number;
  result_image?: string;
  error?: string;
};

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [job, setJob] = useState<JobResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
type HistoryJob = {
  job_id: string;
  filename: string;
  status: string;
  model: string;
  created_at: string;
  completed_at: string | null;
};

const [history, setHistory] = useState<HistoryJob[]>([]);
  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview);
    };
  }, [preview]);
useEffect(() => {
  const loadHistory = async () => {
    try {
      const response = await fetch(`${API_URL}/jobs`);

      if (!response.ok) {
        throw new Error("Failed to load history");
      }

      const data = await response.json();
      setHistory(data);
    } catch (error) {
      console.error("History loading failed:", error);
    }
  };

  loadHistory();
}, []);

  const handleFileChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const selectedFile = event.target.files?.[0];

    if (!selectedFile) return;

    setFile(selectedFile);
    setJob(null);

    if (preview) {
      URL.revokeObjectURL(preview);
    }

    setPreview(URL.createObjectURL(selectedFile));
  };

  const runDetection = async () => {
    if (!file) return;

    setLoading(true);
    setJob(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API_URL}/predict`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Failed to submit image");
      }

      const submittedJob: JobResult = await response.json();
      setJob(submittedJob);

      const pollJob = async () => {
        const resultResponse = await fetch(
          `${API_URL}/jobs/${submittedJob.job_id}`
        );

        if (!resultResponse.ok) {
          throw new Error("Failed to retrieve job");
        }

        const result: JobResult = await resultResponse.json();
        setJob(result);

        if (
          result.status === "completed" ||
          result.status === "failed"
        ) {
          setLoading(false);
          return;
        }

        setTimeout(pollJob, 1000);
      };

      setTimeout(pollJob, 500);
    } catch (error) {
      console.error(error);

      setJob({
        job_id: "",
        status: "failed",
        filename: file.name,
        error: "Could not connect to the backend.",
      });

      setLoading(false);
    }
  };

  const detectionStats = useMemo(() => {
    const detections = job?.detections ?? [];

    const counts: Record<string, number> = {};

    detections.forEach((detection) => {
      counts[detection.class_name] =
        (counts[detection.class_name] || 0) + 1;
    });

    const averageConfidence =
      detections.length > 0
        ? detections.reduce(
            (sum, detection) => sum + detection.confidence,
            0
          ) / detections.length
        : 0;

    return {
      counts,
      averageConfidence,
    };
  }, [job]);

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <div className="mx-auto max-w-7xl px-6 py-12">

        {/* Header */}
        <header className="mb-10">
          <div className="mb-3 flex items-center gap-3">
            <span className="h-2.5 w-2.5 rounded-full bg-blue-500" />

            <p className="text-sm font-medium uppercase tracking-widest text-blue-400">
              AI / Computer Vision
            </p>
          </div>

          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
            Cloud AI/CV Platform
          </h1>

          <p className="mt-4 max-w-3xl text-lg leading-8 text-slate-400">
            Upload an image and run asynchronous object detection
            using a scalable YOLO-powered computer vision pipeline.
          </p>
        </header>

        {/* Main grid */}
        <section className="grid gap-8 lg:grid-cols-2">

          {/* Upload panel */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-8">

            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold">
                  Run inference
                </h2>

                <p className="mt-2 text-sm text-slate-400">
                  JPEG, PNG and WebP supported
                </p>
              </div>

              <div className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-400">
                YOLO
              </div>
            </div>

            <label className="mt-8 flex min-h-72 cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-700 bg-slate-950 p-6 text-center transition hover:border-blue-500">

              {preview ? (
                <img
                  src={preview}
                  alt="Selected image"
                  className="max-h-64 max-w-full rounded-lg object-contain"
                />
              ) : (
                <>
                  <div className="text-4xl text-blue-400">
                    ↑
                  </div>

                  <p className="mt-4 font-medium">
                    Choose an image
                  </p>

                  <p className="mt-2 text-sm text-slate-500">
                    Click to browse files
                  </p>
                </>
              )}

              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                className="hidden"
                onChange={handleFileChange}
              />
            </label>

            {file && (
              <div className="mt-4 rounded-lg bg-slate-950 px-4 py-3">
                <p className="truncate text-sm text-slate-300">
                  {file.name}
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            )}

            <button
              onClick={runDetection}
              disabled={!file || loading}
              className="mt-6 w-full rounded-xl bg-blue-600 px-5 py-3.5 font-semibold transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-500"
            >
              {loading ? "Processing inference..." : "Run Detection"}
            </button>

            {job?.status === "queued" && (
              <div className="mt-4 rounded-lg border border-blue-900 bg-blue-950/30 px-4 py-3 text-sm text-blue-300">
                Job submitted. Waiting for the CV worker...
              </div>
            )}

            {job?.status === "failed" && (
              <div className="mt-4 rounded-lg border border-red-900 bg-red-950/30 px-4 py-3 text-sm text-red-300">
                {job.error || "Inference failed."}
              </div>
            )}

          </div>

          {/* Result image */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-8">

            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold">
                  Detection Results
                </h2>

                <p className="mt-2 text-sm text-slate-400">
                  YOLO annotated output
                </p>
              </div>

              {job?.status === "completed" && (
                <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-400">
                  Completed
                </span>
              )}
            </div>

            {job?.status === "completed" && job.result_image ? (
              <div className="mt-8">

                <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-950">
                  <img
                    src={`${API_URL}${job.result_image}`}
                    alt="YOLO detection result"
                    className="w-full object-contain"
                  />
                </div>

                <a
                  href={`${API_URL}${job.result_image}`}
                  download={`${job.filename}-result.jpg`}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-4 block w-full rounded-xl border border-slate-700 px-5 py-3 text-center text-sm font-semibold transition hover:border-blue-500 hover:text-blue-400"
                >
                  Download Annotated Result
                </a>

              </div>
            ) : (
              <div className="mt-8 flex min-h-72 items-center justify-center rounded-xl bg-slate-950">

                {loading ? (
                  <div className="text-center">
                    <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-slate-700 border-t-blue-500" />

                    <p className="mt-4 text-sm text-slate-400">
                      Running computer vision inference...
                    </p>
                  </div>
                ) : (
                  <p className="text-sm text-slate-500">
                    Upload an image to see results
                  </p>
                )}

              </div>
            )}

          </div>

        </section>

        {/* Summary */}
        {job?.status === "completed" && (
          <>
            <section className="mt-8 grid gap-4 sm:grid-cols-3">

              <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
                <p className="text-sm text-slate-400">
                  Objects detected
                </p>

                <p className="mt-2 text-3xl font-bold">
                  {job.detection_count ?? 0}
                </p>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
                <p className="text-sm text-slate-400">
                  Object classes
                </p>

                <p className="mt-2 text-3xl font-bold">
                  {Object.keys(detectionStats.counts).length}
                </p>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
                <p className="text-sm text-slate-400">
                  Average confidence
                </p>

                <p className="mt-2 text-3xl font-bold">
                  {(detectionStats.averageConfidence * 100).toFixed(1)}%
                </p>
              </div>

            </section>

            {/* Detection breakdown */}
            <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-8">

              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold">
                    Detection Breakdown
                  </h2>

                  <p className="mt-2 text-sm text-slate-400">
                    Objects identified by the model
                  </p>
                </div>

                <span className="text-sm text-slate-500">
                  {job.detection_count} total
                </span>
              </div>

              <div className="mt-8 space-y-5">

                {Object.entries(detectionStats.counts)
                  .sort(([, a], [, b]) => b - a)
                  .map(([className, count]) => {

                    const percentage =
                      job.detection_count
                        ? (count / job.detection_count) * 100
                        : 0;

                    return (
                      <div key={className}>

                        <div className="mb-2 flex items-center justify-between">

                          <span className="font-medium capitalize">
                            {className}
                          </span>

                          <span className="text-sm text-slate-400">
                            {count}
                          </span>

                        </div>

                        <div className="h-2 overflow-hidden rounded-full bg-slate-800">

                          <div
                            className="h-full rounded-full bg-blue-500"
                            style={{
                              width: `${percentage}%`,
                            }}
                          />

                        </div>

                      </div>
                    );
                  })}

              </div>

            </section>

            {/* Detailed detections */}
            <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-8">

              <h2 className="text-xl font-semibold">
                Detailed Detections
              </h2>

              <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">

                {(job.detections ?? []).map(
                  (detection, index) => (
                    <div
                      key={`${detection.class_name}-${index}`}
                      className="rounded-xl border border-slate-800 bg-slate-950 p-5"
                    >

                      <div className="flex items-center justify-between">

                        <span className="text-lg font-semibold capitalize">
                          {detection.class_name}
                        </span>

                        <span className="rounded-full bg-blue-500/10 px-3 py-1 text-sm text-blue-400">
                          {(detection.confidence * 100).toFixed(1)}%
                        </span>

                      </div>

                      <p className="mt-4 text-xs uppercase tracking-wide text-slate-500">
                        Bounding box
                      </p>

                      <p className="mt-1 text-sm text-slate-400">
                        ({detection.bounding_box.x1.toFixed(0)},{" "}
                        {detection.bounding_box.y1.toFixed(0)}) →
                        ({detection.bounding_box.x2.toFixed(0)},{" "}
                        {detection.bounding_box.y2.toFixed(0)})
                      </p>

                    </div>
                  )
                )}

              </div>

            </section>

            {/* Job metadata */}
            <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-8">

              <h2 className="text-xl font-semibold">
                Inference Metadata
              </h2>

              <div className="mt-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">

                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">
                    Job ID
                  </p>

                  <p className="mt-2 break-all text-sm text-slate-300">
                    {job.job_id}
                  </p>
                </div>

                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">
                    Filename
                  </p>

                  <p className="mt-2 text-sm text-slate-300">
                    {job.filename}
                  </p>
                </div>

                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">
                    Model
                  </p>

                  <p className="mt-2 text-sm text-slate-300">
                    YOLO11n
                  </p>
                </div>

                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">
                    Status
                  </p>

                  <p className="mt-2 text-sm text-emerald-400">
                    {job.status}
                  </p>
                </div>

              </div>

            </section>
          </>
        )}

        {/* Architecture cards */}
        <section className="mt-8 grid gap-4 sm:grid-cols-3">

          <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
            <p className="text-sm text-slate-400">
              Inference Engine
            </p>

            <p className="mt-2 text-lg font-semibold">
              YOLO
            </p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
            <p className="text-sm text-slate-400">
              Backend
            </p>

            <p className="mt-2 text-lg font-semibold">
              FastAPI
            </p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
            <p className="text-sm text-slate-400">
              Processing
            </p>

            <p className="mt-2 text-lg font-semibold">
              Async Jobs
            </p>
          </div>

        </section>

     </div>
<section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900/70 p-8">
  <div className="mb-6 flex items-center justify-between">
    <div>
      <p className="text-sm uppercase tracking-wider text-blue-400">
        PostgreSQL
      </p>
      <h2 className="mt-1 text-2xl font-semibold text-white">
        Inference History
      </h2>
    </div>

    <span className="rounded-full border border-slate-700 px-3 py-1 text-sm text-slate-400">
      {history.length} jobs
    </span>
  </div>

  {history.length === 0 ? (
    <div className="rounded-xl border border-dashed border-slate-700 p-8 text-center text-slate-500">
      No inference jobs yet.
    </div>
  ) : (
    <div className="overflow-x-auto">
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-slate-800 text-sm text-slate-500">
            <th className="px-4 py-3">File</th>
            <th className="px-4 py-3">Model</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Created</th>
            <th className="px-4 py-3">Completed</th>
          </tr>
        </thead>

        <tbody>
          {history.map((item) => (
            <tr
              key={item.job_id}
              className="border-b border-slate-800/70 text-sm"
            >
              <td className="px-4 py-4 font-medium text-white">
                {item.filename}
              </td>

              <td className="px-4 py-4 text-slate-400">
                {item.model}
              </td>

              <td className="px-4 py-4">
                <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-emerald-400">
                  {item.status}
                </span>
              </td>

              <td className="px-4 py-4 text-slate-400">
                {new Date(item.created_at).toLocaleString()}
              </td>

              <td className="px-4 py-4 text-slate-400">
                {item.completed_at
                  ? new Date(item.completed_at).toLocaleString()
                  : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )}
</section>
 </main>
  );
}

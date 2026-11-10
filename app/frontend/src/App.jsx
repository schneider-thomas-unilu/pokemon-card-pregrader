import { useEffect, useRef, useState } from "react";

const defectLabels = {
  corner_wear: "Corner wear",
  edge_wear: "Edge wear",
  surface_scratch: "Surface scratches",
  card_bending: "Card bending",
  other_visible_issue: "Other visible issue",
};

function landmarkPath(points, size) {
  if (!size || points.length < 2) return "";
  return `${points.map(([x, y], index) => `${index === 0 ? "M" : "L"} ${(x / size.width) * 100} ${(y / size.height) * 100}`).join(" ")}${points.length === 4 ? " Z" : ""}`;
}

export default function App() {
  const uploadInput = useRef(null);
  const cameraVideo = useRef(null);
  const cameraStream = useRef(null);
  const errorCloseButton = useRef(null);
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [imageSize, setImageSize] = useState(null);
  const [outer, setOuter] = useState([]);
  const [innerCorners, setInnerCorners] = useState([]);
  const [activeLandmark, setActiveLandmark] = useState("outer");
  const [includeAi, setIncludeAi] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [cameraOpen, setCameraOpen] = useState(false);
  const [cameraError, setCameraError] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!error) return undefined;
    errorCloseButton.current?.focus();
    function dismissOnEscape(event) {
      if (event.key === "Escape") setError("");
    }
    window.addEventListener("keydown", dismissOnEscape);
    return () => window.removeEventListener("keydown", dismissOnEscape);
  }, [error]);

  function setPhoto(selected) {
    if (!selected) return;
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setFile(selected);
    setPreviewUrl(URL.createObjectURL(selected));
    setImageSize(null);
    setOuter([]);
    setInnerCorners([]);
    setActiveLandmark("outer");
    setResult(null);
    setError("");
    setConfirmed(false);
  }

  function chooseFile(event) {
    const selected = event.target.files?.[0];
    event.target.value = "";
    setPhoto(selected);
  }

  function closeCamera() {
    cameraStream.current?.getTracks().forEach((track) => track.stop());
    cameraStream.current = null;
    setCameraOpen(false);
    setCameraError("");
  }

  useEffect(() => {
    if (!cameraOpen) return undefined;
    let cancelled = false;

    async function startCamera() {
      if (!navigator.mediaDevices?.getUserMedia) {
        setCameraError("This browser cannot open a camera here. Try a supported browser on HTTPS or localhost.");
        return;
      }
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: "environment" } },
          audio: false,
        });
        if (cancelled) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }
        cameraStream.current = stream;
        if (cameraVideo.current) cameraVideo.current.srcObject = stream;
      } catch {
        if (!cancelled) setCameraError("Camera access was blocked or no camera is available. Check browser permissions and try again.");
      }
    }

    startCamera();
    return () => {
      cancelled = true;
      cameraStream.current?.getTracks().forEach((track) => track.stop());
      cameraStream.current = null;
    };
  }, [cameraOpen]);

  function capturePhoto() {
    const video = cameraVideo.current;
    if (!video?.videoWidth || !video.videoHeight) {
      setCameraError("The camera is still starting. Please try again in a moment.");
      return;
    }
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext("2d");
    if (!context) {
      setCameraError("Could not capture the photo. Please try again.");
      return;
    }
    context.drawImage(video, 0, 0);
    canvas.toBlob((blob) => {
      if (!blob || !cameraStream.current) {
        setCameraError("Could not capture the photo. Please try again.");
        return;
      }
      setPhoto(new File([blob], `card-${Date.now()}.jpg`, { type: "image/jpeg" }));
      closeCamera();
    }, "image/jpeg", 0.92);
  }

  function selectLandmark(event) {
    const activePoints = activeLandmark === "outer" ? outer : innerCorners;
    if (!previewUrl || activePoints.length >= 4) return;
    const bounds = event.currentTarget.getBoundingClientRect();
    const naturalWidth = event.currentTarget.naturalWidth;
    const naturalHeight = event.currentTarget.naturalHeight;
    if (!naturalWidth || !naturalHeight) return;
    const x = ((event.clientX - bounds.left) / bounds.width) * naturalWidth;
    const y = ((event.clientY - bounds.top) / bounds.height) * naturalHeight;
    const point = [Number(x.toFixed(2)), Number(y.toFixed(2))];
    if (activeLandmark === "outer") {
      setOuter((points) => [...points, point]);
      if (outer.length === 3) setActiveLandmark("inner");
    } else {
      setInnerCorners((points) => [...points, point]);
    }
    setResult(null);
    setError("");
  }

  function resetActivePoints() {
    setOuter([]);
    setInnerCorners([]);
    setActiveLandmark("outer");
    setResult(null);
  }

  async function submit(event) {
    event.preventDefault();
    setError("");
    setResult(null);
    if (!file) return setError("Choose a card photo first.");
    if (outer.length !== 4) {
      return setError("Mark all four outside corners of the card.");
    }
    if (innerCorners.length !== 4) {
      return setError("Mark all four corners of the inner printed border.");
    }
    if (!confirmed) return setError("Confirm that the full card is visible and the photo is yours to analyze.");
    if (includeAi && !window.confirm("The card photo will be sent to the configured vision provider for analysis. Continue?")) {
      return;
    }

    const data = new FormData();
    data.append("image_file", file);
    data.append("card_corners", JSON.stringify(outer));
    data.append("inner_corners", JSON.stringify(innerCorners));
    data.append("include_ai", String(includeAi));

    setBusy(true);
    try {
      const response = await fetch("/api/analyze", { method: "POST", body: data });
      const responseText = await response.text();
      let body = null;
      if (responseText) {
        try {
          body = JSON.parse(responseText);
        } catch {
          if (response.ok) {
            throw new Error("The analysis service returned an unreadable response. Please try again.");
          }
        }
      }
      if (!response.ok) {
        const detail = body?.detail;
        if (typeof detail === "string") throw new Error(detail);
        if (detail && typeof detail === "object" && !Array.isArray(detail)) {
          const reasons = Array.isArray(detail.retake_reasons) ? detail.retake_reasons.join(" ") : "";
          const providerBody = typeof detail.provider_response_body === "string"
            ? `Gemini response body:\n${detail.provider_response_body}`
            : "";
          if (detail.message || reasons || providerBody) {
            throw new Error([detail.message, reasons, providerBody].filter(Boolean).join("\n\n"));
          }
        }
        if (Array.isArray(detail)) {
          const messages = detail.map((item) => item?.msg).filter(Boolean);
          if (messages.length) throw new Error(messages.join(" "));
        }
        const statusMessages = {
          413: "This photo is too large to upload. Choose a smaller image and try again.",
          415: "This photo format isn’t supported. Use a JPEG, PNG, or WebP image.",
          502: "The optional photo-analysis provider could not complete the request. Please try again later.",
          503: "The optional photo-analysis service is not configured right now.",
        };
        throw new Error(
          statusMessages[response.status]
            ?? `The analysis service returned an error (HTTP ${response.status}). Please try again.`,
        );
      }
      if (!body || typeof body !== "object") {
        throw new Error("The analysis service returned an empty response. Please try again.");
      }
      setResult(body);
    } catch (requestError) {
      setError(
        requestError instanceof TypeError
          ? "Could not connect to the analysis service. Check that the app is running and try again."
          : requestError instanceof Error
            ? requestError.message
            : "An unexpected error interrupted the review. Please try again.",
      );
    } finally {
      setBusy(false);
    }
  }

  const outerPath = landmarkPath(outer, imageSize);
  const innerPath = landmarkPath(innerCorners, imageSize);

  return (
    <main className="shell">
      <header className="topbar">
        <a className="brand" href="#" aria-label="A-Eye home">
          <span className="brand-mark">A</span>
          <span>A-Eye</span>
        </a>
      </header>

      <form className="workspace" onSubmit={submit}>
        <section className="panel photo-panel">
          <div className="photo-heading">
            <p className="photo-formats">JPG, PNG or WebP · front of card</p>
            {previewUrl && <button type="button" className="change-photo" onClick={() => uploadInput.current?.click()}>Change photo</button>}
          </div>
          {!previewUrl ? (
            <div className="dropzone">
              <span className="upload-icon">↑</span>
              <strong>Choose how to add your card</strong>
              <span>Front-facing, evenly lit, fully in view</span>
              <div className="photo-actions">
                <button type="button" className="browse" onClick={() => uploadInput.current?.click()}>↑ &nbsp; Upload a photo</button>
                <button type="button" className="camera-button" onClick={() => { setCameraError(""); setCameraOpen(true); }}>▣ &nbsp; Take a picture</button>
            </div>
              <span className="photo-hint">A clear, straight-on photo helps make the review more useful.</span>
              </div>
          ) : (
            <div className="image-stage">
              <div className="image-frame">
                <img src={previewUrl} alt="Uploaded card; click to mark the requested corners" onClick={selectLandmark} onLoad={(event) => setImageSize({ width: event.currentTarget.naturalWidth, height: event.currentTarget.naturalHeight })} />
                <div className="image-overlay">
                  {(outerPath || innerPath) && (
                    <svg className="image-outline" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
                      {outerPath && <path className="card-outline-halo" d={outerPath} />}
                      {outerPath && <path className="card-outline-line" d={outerPath} />}
                      {innerPath && <path className="inner-outline-line" d={innerPath} />}
                    </svg>
                  )}
                  {outer.map((point, index) => <span className="marker outer-marker" key={`o${index}`} style={{ left: `${imageSize ? point[0] / imageSize.width * 100 : 0}%`, top: `${imageSize ? point[1] / imageSize.height * 100 : 0}%` }} />)}
                  {innerCorners.map((point, index) => <span className="marker inner-marker" key={`i${index}`} style={{ left: `${imageSize ? point[0] / imageSize.width * 100 : 0}%`, top: `${imageSize ? point[1] / imageSize.height * 100 : 0}%` }} />)}
                </div>
              </div>
            </div>
          )}
          {file && (
            <div className="landmark-controls">
              <div className="landmark-topline">
                <div><strong>Mark the card borders, clockwise</strong></div>
              </div>
              <div className="mark-actions">
                <button type="button" className={`mark-tab${activeLandmark === "outer" ? " active" : ""}`} onClick={() => setActiveLandmark("outer")}>Outside corners ({outer.length}/4)</button>
                <button type="button" className={`mark-tab${activeLandmark === "inner" ? " active" : ""}`} onClick={() => setActiveLandmark("inner")} disabled={outer.length !== 4}>Inner printed border ({innerCorners.length}/4)</button>
                <button type="button" className="text-button" onClick={resetActivePoints}>Reset points</button>
              </div>
              <p className="next-point">
                {activeLandmark === "outer"
                  ? outer.length < 4
                    ? "Tap the outside corners, starting at the top-left and moving clockwise."
                    : "Outside corners are marked. Select the inner printed border to continue."
                  : innerCorners.length < 4
                    ? "Tap the inner border corners, starting at the top-left and moving clockwise."
                    : "Both borders are marked. Review the outlines, then build your card review."}
              </p>
              <label className="confirm-line">
                <input type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} />
                <span>The entire card is visible and I have permission to analyze this photo.</span>
              </label>
            </div>
          )}
        </section>

        <aside className="side-column">
          <section className="panel review-method-panel">
              <p className="panel-copy">The report explains the photo checks and anything the optional condition review can see.</p>
            <div className="method-list">
              <div><span aria-hidden="true">•</span><p><strong>Photo quality</strong><small>Basic size, lighting and focus checks.</small></p></div>
              <div><span aria-hidden="true">•</span><p><strong>Card outline</strong><small>Your outside corners mark the card’s visible boundary.</small></p></div>
              <div><span aria-hidden="true">•</span><p><strong>Centering</strong><small>Outside and inner-border corners estimate opposing margins.</small></p></div>
              <div><span aria-hidden="true">•</span><p><strong>Visible condition</strong><small>Optional observations with evidence and uncertainty.</small></p></div>
            </div>
            <label className="ai-toggle">
              <input type="checkbox" checked={includeAi} onChange={(event) => setIncludeAi(event.target.checked)} />
              <span><strong>Include a photo condition review</strong><small>Your photo is sent to Gemini only if you select this and confirm.</small></span>
              <span className="toggle-indicator" />
            </label>
            <button type="submit" className="analyze-button" disabled={busy || !file}>
              {busy ? "Building your review…" : "Build my card review"} <span>↗</span>
            </button>
            <p className="privacy-note">Your photo isn’t stored here. This is a visual guide, not a professional grade.</p>
          </section>
        </aside>
      </form>

      <input ref={uploadInput} hidden type="file" accept="image/jpeg,image/png,image/webp" onChange={chooseFile} />
      {error && (
        <div className="error-backdrop">
          <section className="error-dialog" role="alertdialog" aria-modal="true" aria-labelledby="error-title" aria-describedby="error-description">
            <div className="error-heading">
              <span className="error-symbol" aria-hidden="true">!</span>
              <h2 id="error-title">Couldn’t complete the review</h2>
            </div>
            <p id="error-description">{error}</p>
            <button ref={errorCloseButton} type="button" className="error-dismiss" onClick={() => setError("")}>Close</button>
          </section>
        </div>
      )}
      {cameraOpen && (
        <div className="camera-backdrop">
          <section className="camera-dialog" role="dialog" aria-modal="true" aria-labelledby="camera-title">
            <div className="camera-heading"><h2 id="camera-title">Take a card photo</h2><button type="button" aria-label="Close camera" onClick={closeCamera}>×</button></div>
            {cameraError ? <p className="camera-error" role="alert">{cameraError}</p> : <video ref={cameraVideo} autoPlay playsInline muted />}
            <div className="camera-actions">
              <button type="button" className="camera-cancel" onClick={closeCamera}>Cancel</button>
              <button type="button" className="camera-capture" onClick={capturePhoto} disabled={Boolean(cameraError)}>Take picture</button>
            </div>
          </section>
        </div>
      )}
      {result && <Result result={result} />}
      <footer>
        <span>Preliminary observations only—not an official grade or financial guarantee.</span>
      </footer>
    </main>
  );
}

function Result({ result }) {
  const centering = result.centering;
  return (
    <section className="results">
      <div className="results-header"><h2>Review and supporting evidence</h2><span className="quality-badge"><i /> PHOTO CHECK PASSED</span></div>
      <article className="result-card">
        <h3>Card outline</h3>
        <p>The four marked outside corners identify the card and correct perspective for the centering estimate.</p>
      </article>
      <article className="result-card centering-card">
        <h3>Centering estimate</h3>
        <p>Opposing inner-border margins are compared after correcting the card’s perspective.</p>
        <div className="centering-ratios">
          <div><span>Left : right</span><strong>{centering.left_right_ratio}</strong><small>{centering.left_margin_percent}% : {centering.right_margin_percent}% of card width</small></div>
          <div><span>Top : bottom</span><strong>{centering.top_bottom_ratio}</strong><small>{centering.top_margin_percent}% : {centering.bottom_margin_percent}% of card height</small></div>
        </div>
      </article>
      <article className="result-card vision-card">
        <div><h3>Photo observations</h3></div>
        {!result.vision ? <p className="no-ai">The optional photo condition review wasn’t used. This report includes basic photo checks, the card outline, and a centering estimate; surface and edge condition were not assessed.</p> : (
          <>
            <div className="defect-list">{Object.entries(result.vision.defects).map(([type, defect]) => (
              <div className="defect" key={type}>
                <span className={defect.present ? "defect-state observed" : "defect-state"}>{defect.present ? "Possible" : "Not seen"}</span>
                <div><strong>{defectLabels[type]}</strong><p>{defect.evidence || "No visible evidence noted."}</p></div>
                <span className="confidence">{(defect.confidence * 100).toFixed(0)}%</span>
              </div>
            ))}</div>
            <p>Model-reported confidence is not a calibrated probability.</p>
          </>
        )}
      </article>
      <article className="result-card explanation-card">
        <h3>What each part means</h3>
        <div className="explanation-list">
          {result.review_basis.map((item) => (
            <div className="explanation-item" key={item.factor}>
              <span className="explanation-bullet" aria-hidden="true" />
              <div><strong>{item.factor}</strong><p>{item.explanation}</p><small>{item.result}</small></div>
            </div>
          ))}
        </div>
        <p className="grade-caveat">{result.grade_note}</p>
      </article>
      <div className="limitations"><strong>Keep in mind</strong><ul>{result.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}</ul></div>
    </section>
  );
}

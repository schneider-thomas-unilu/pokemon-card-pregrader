import { useMemo, useRef, useState } from "react";

const pointLabels = [
  "Top-left",
  "Top-right",
  "Bottom-right",
  "Bottom-left",
];
const defectLabels = {
  corner_wear: "Corner wear",
  edge_wear: "Edge wear",
  surface_scratch: "Surface scratches",
  bend_or_crease: "Bend or crease",
  other_visible_issue: "Other visible issue",
};
const defaults = {
  raw_sale: "30",
  grade_7_sale: "45",
  grade_8_sale: "70",
  grading_fee: "20",
  shipping: "8",
  selling_cost: "3",
};

function money(value) {
  return new Intl.NumberFormat("en-IE", {
    style: "currency",
    currency: "EUR",
  }).format(value);
}

export default function App() {
  const uploadInput = useRef(null);
  const cameraInput = useRef(null);
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [imageSize, setImageSize] = useState(null);
  const [outer, setOuter] = useState([]);
  const [inner, setInner] = useState([]);
  const [activeGroup, setActiveGroup] = useState("outer");
  const [assumptions, setAssumptions] = useState(defaults);
  const [includeAi, setIncludeAi] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const activePoints = activeGroup === "outer" ? outer : inner;
  const progress = useMemo(
    () => `${outer.length}/4 card corners · ${inner.length}/4 inner-border corners`,
    [outer.length, inner.length],
  );

  function chooseFile(event) {
    const selected = event.target.files?.[0];
    event.target.value = "";
    if (!selected) return;
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setFile(selected);
    setPreviewUrl(URL.createObjectURL(selected));
    setImageSize(null);
    setOuter([]);
    setInner([]);
    setResult(null);
    setError("");
    setConfirmed(false);
  }

  function selectLandmark(event) {
    if (!previewUrl || activePoints.length >= 4) return;
    const bounds = event.currentTarget.getBoundingClientRect();
    const naturalWidth = event.currentTarget.naturalWidth;
    const naturalHeight = event.currentTarget.naturalHeight;
    const x = ((event.clientX - bounds.left) / bounds.width) * naturalWidth;
    const y = ((event.clientY - bounds.top) / bounds.height) * naturalHeight;
    const update = activeGroup === "outer" ? setOuter : setInner;
    update((points) => [...points, [Number(x.toFixed(2)), Number(y.toFixed(2))]]);
    setResult(null);
    setError("");
  }

  function resetActivePoints() {
    if (activeGroup === "outer") setOuter([]);
    else setInner([]);
    setResult(null);
  }

  function setAssumption(name, value) {
    setAssumptions((current) => ({ ...current, [name]: value }));
    setResult(null);
  }

  async function submit(event) {
    event.preventDefault();
    setError("");
    setResult(null);
    if (!file) return setError("Choose a card photo first.");
    if (outer.length !== 4 || inner.length !== 4) {
      return setError("Mark all four card corners and all four inner-border corners.");
    }
    if (!confirmed) return setError("Confirm that the full card is visible and the photo is yours to analyze.");
    if (includeAi && !window.confirm("The card photo will be sent to the configured vision provider for analysis. Continue?")) {
      return;
    }

    const data = new FormData();
    data.append("image_file", file);
    data.append("outer_corners", JSON.stringify(outer));
    data.append("inner_corners", JSON.stringify(inner));
    data.append("include_ai", String(includeAi));
    Object.entries(assumptions).forEach(([key, value]) => data.append(key, value));

    setBusy(true);
    try {
      const response = await fetch("/api/analyze", { method: "POST", body: data });
      const body = await response.json();
      if (!response.ok) {
        const detail = body.detail;
        throw new Error(
          typeof detail === "string"
            ? detail
            : `${detail?.message ?? "Analysis failed."} ${(detail?.retake_reasons ?? []).join(" ")}`,
        );
      }
      setResult(body);
    } catch (requestError) {
      setError(requestError.message || "Could not reach the analysis service.");
    } finally {
      setBusy(false);
    }
  }

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
          <div className="panel-heading">
            <div><span className="step">01 — YOUR PHOTO</span><h2>Start with a clear view</h2></div>
            <span className="optional">JPG · PNG · WEBP</span>
          </div>
          {!previewUrl ? (
            <div className="dropzone">
              <span className="upload-icon">↑</span>
              <strong>Choose how to add your card</strong>
              <span>Front-facing, evenly lit, fully in view</span>
              <div className="photo-actions">
                <button type="button" className="browse" onClick={() => uploadInput.current?.click()}>↑ &nbsp; Upload a photo</button>
                <button type="button" className="camera-button" onClick={() => cameraInput.current?.click()}>▣ &nbsp; Take a picture</button>
              </div>
              <span className="photo-hint">Camera option works on supported phones and browsers</span>
            </div>
          ) : (
            <div className="image-stage">
              <div className="image-frame">
                <img src={previewUrl} alt="Uploaded card; click to mark the requested corners" onClick={selectLandmark} onLoad={(event) => setImageSize({ width: event.currentTarget.naturalWidth, height: event.currentTarget.naturalHeight })} />
                <div className="image-overlay">
                  {outer.map((point, index) => <span className="marker outer-marker" key={`o${index}`} style={{ left: `${imageSize ? point[0] / imageSize.width * 100 : 0}%`, top: `${imageSize ? point[1] / imageSize.height * 100 : 0}%` }}>{index + 1}</span>)}
                  {inner.map((point, index) => <span className="marker inner-marker" key={`i${index}`} style={{ left: `${imageSize ? point[0] / imageSize.width * 100 : 0}%`, top: `${imageSize ? point[1] / imageSize.height * 100 : 0}%` }}>{index + 1}</span>)}
                </div>
              </div>
              <button type="button" className="change-photo" onClick={() => uploadInput.current?.click()}>Change photo</button>
            </div>
          )}
          {file && (
            <div className="landmark-controls">
              <div className="landmark-topline">
                <div><span className="step">02 — CENTERING</span><strong>Mark the corners, clockwise</strong></div>
                <span className="progress">{progress}</span>
              </div>
              <div className="mark-actions">
                <button type="button" className={activeGroup === "outer" ? "mark-tab active" : "mark-tab"} onClick={() => setActiveGroup("outer")}>Card edge</button>
                <button type="button" className={activeGroup === "inner" ? "mark-tab active" : "mark-tab"} onClick={() => setActiveGroup("inner")}>Printed border</button>
                <button type="button" className="text-button" onClick={resetActivePoints}>Reset {activeGroup === "outer" ? "card edge" : "border"}</button>
              </div>
              <p className="next-point">Next point <strong>{activePoints.length < 4 ? pointLabels[activePoints.length] : "Complete"}</strong><span>{activeGroup === "outer" ? "Mark the card’s outside edge" : "Mark the inner printed border"}</span></p>
              <label className="confirm-line">
                <input type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} />
                <span>The entire card is visible and I have permission to analyze this photo.</span>
              </label>
            </div>
          )}
        </section>

        <aside className="side-column">
          <section className="panel estimate-panel">
            <div className="panel-heading">
              <div><span className="step">03 — YOUR NUMBERS</span><h2>Does grading add up?</h2></div>
              <span className="currency">EUR €</span>
            </div>
            <p className="panel-copy">A quick net comparison, based on the prices and costs you expect.</p>
            <div className="value-grid">
              <MoneyField label="Sell raw for" name="raw_sale" value={assumptions.raw_sale} onChange={setAssumption} />
              <MoneyField label="If graded 7" name="grade_7_sale" value={assumptions.grade_7_sale} onChange={setAssumption} />
              <MoneyField label="If graded 8" name="grade_8_sale" value={assumptions.grade_8_sale} onChange={setAssumption} />
              <MoneyField label="Grading fee" name="grading_fee" value={assumptions.grading_fee} onChange={setAssumption} />
              <MoneyField label="Shipping" name="shipping" value={assumptions.shipping} onChange={setAssumption} />
              <MoneyField label="Selling costs" name="selling_cost" value={assumptions.selling_cost} onChange={setAssumption} />
            </div>
            <label className="ai-toggle">
              <input type="checkbox" checked={includeAi} onChange={(event) => setIncludeAi(event.target.checked)} />
              <span><strong>Include AI visual observations</strong><small>Photo is sent to the configured Gemini provider. Optional.</small></span>
              <span className="toggle-indicator" />
            </label>
            <button type="submit" className="analyze-button" disabled={busy || !file}>
              {busy ? "Reviewing your card…" : "Review this card"} <span>↗</span>
            </button>
            <p className="privacy-note">Photos are processed in memory and not stored by this app.</p>
          </section>
          {error && <div className="error-box" role="alert"><strong>Couldn’t complete the review</strong><span>{error}</span></div>}
        </aside>
      </form>

      <input ref={uploadInput} hidden type="file" accept="image/jpeg,image/png,image/webp" onChange={chooseFile} />
      <input ref={cameraInput} hidden type="file" accept="image/jpeg,image/png,image/webp" capture="environment" onChange={chooseFile} />
      {result && <Result result={result} />}
      <footer>
        <a className="footer-brand" href="#" aria-label="A-Eye home"><span className="brand-mark">A</span> A-Eye</a>
        <span>PRELIMINARY OBSERVATIONS ONLY · NOT AN OFFICIAL GRADE OR FINANCIAL GUARANTEE</span>
      </footer>
    </main>
  );
}

function MoneyField({ label, name, value, onChange }) {
  return <label className="money-field"><span>{label}</span><div><span>€</span><input type="number" min="0" step="0.01" required value={value} onChange={(event) => onChange(name, event.target.value)} /></div></label>;
}

function Result({ result }) {
  const comparison = result.profit_comparison;
  return (
    <section className="results">
      <div className="results-header"><div><span className="step">YOUR CARD REPORT</span><h2>Here’s what we found.</h2></div><span className="quality-badge"><i /> PHOTO CHECK PASSED</span></div>
      <div className="results-grid">
        <article className="result-card centering-card">
          <span className="result-label">01 / GEOMETRY</span>
          <h3>Centering</h3>
          <div className="ratio-row"><span>Left : right</span><strong>{result.centering.left_right_ratio}</strong></div>
          <div className="ratio-row"><span>Top : bottom</span><strong>{result.centering.top_bottom_ratio}</strong></div>
          <p>Measured from your corner selections after perspective correction.</p>
        </article>
        <article className="result-card economics-card">
          <span className="result-label">02 / NET COMPARISON</span>
          <h3>Sell raw or submit?</h3>
          <div className="ratio-row"><span>Sell raw</span><strong>{money(comparison.raw_net)}</strong></div>
          {Object.entries(comparison.graded_net_by_grade).map(([grade, net]) => <div className="ratio-row" key={grade}><span>If graded {grade}</span><strong>{money(net)}</strong></div>)}
          <div className="recommendation">{comparison.recommendation}</div>
          <p>{comparison.disclaimer}</p>
        </article>
      </div>
      <article className="result-card vision-card">
        <div><span className="result-label">03 / VISIBLE CONDITION</span><h3>What the photo may show</h3></div>
        {!result.vision ? <p className="no-ai">AI observations weren’t requested. Centering and the price comparison are still available.</p> : (
          <>
            <div className="defect-list">{result.vision.defects.map((defect) => (
              <div className="defect" key={defect.type}>
                <span className={defect.observed ? "defect-state observed" : "defect-state"}>{defect.observed ? "Possible" : "Not seen"}</span>
                <div><strong>{defectLabels[defect.type]}</strong><p>{defect.evidence || "No visible evidence noted."}</p></div>
                <span className="confidence">{defect.confidence}</span>
              </div>
            ))}</div>
            <p>{result.vision.confidence_note}</p>
          </>
        )}
      </article>
      <div className="limitations"><strong>Keep in mind</strong><ul>{result.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}</ul></div>
    </section>
  );
}

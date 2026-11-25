# Serve a folder on http://localhost:<Port>/ so the in-app browser can run the diagram's script
# (it will not run scripts in a file:// page). Stops by itself after -Minutes. No dependencies.
#
#   powershell -File serve.ps1 -Root C:\path\to\folder [-Port 8765] [-Minutes 30]
#
# Elsewhere, `python3 -m http.server 8765 --directory <folder>` does the same job.
param(
  [string]$Root = (Get-Location).Path,
  [int]$Port = 8765,
  [int]$Minutes = 30
)
$types = @{ '.html' = 'text/html; charset=utf-8'; '.js' = 'text/javascript; charset=utf-8'; '.css' = 'text/css; charset=utf-8'; '.json' = 'application/json'; '.svg' = 'image/svg+xml'; '.png' = 'image/png' }
$listener = [System.Net.HttpListener]::new()
$listener.Prefixes.Add("http://localhost:$Port/")
$listener.Start()
Write-Output "Serving $Root on http://localhost:$Port/ for $Minutes minutes"
$deadline = (Get-Date).AddMinutes($Minutes)
try {
  while ($listener.IsListening -and (Get-Date) -lt $deadline) {
    $task = $listener.GetContextAsync()
    while (-not $task.Wait(1000)) { if ((Get-Date) -ge $deadline) { break } }
    if (-not $task.IsCompleted) { break }
    $ctx = $task.Result
    $rel = [Uri]::UnescapeDataString($ctx.Request.Url.AbsolutePath.TrimStart('/'))
    $path = [IO.Path]::GetFullPath((Join-Path $Root $rel))
    $ext = [IO.Path]::GetExtension($path).ToLowerInvariant()
    if ($path.StartsWith([IO.Path]::GetFullPath($Root)) -and (Test-Path $path -PathType Leaf) -and $types.ContainsKey($ext)) {
      $bytes = [IO.File]::ReadAllBytes($path)
      $ctx.Response.ContentType = $types[$ext]
      $ctx.Response.Headers.Add('Cache-Control', 'no-store')
      $ctx.Response.OutputStream.Write($bytes, 0, $bytes.Length)
    } else {
      $ctx.Response.StatusCode = 404
    }
    $ctx.Response.Close()
  }
} finally {
  $listener.Stop()
}

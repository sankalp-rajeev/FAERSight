$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$toolsPath = Join-Path $projectRoot '.tools/weka'
New-Item -ItemType Directory -Force -Path $toolsPath | Out-Null

$artifacts = @(
    @{
        Name = 'weka-stable-3.8.6.jar'
        Url = 'https://repo.maven.apache.org/maven2/nz/ac/waikato/cms/weka/weka-stable/3.8.6/weka-stable-3.8.6.jar'
        SHA256 = '932ea2f342b58fe45736389e9c426d5b5955e610d1f5f6485117f532068915e9'
    },
    @{
        Name = 'bounce-0.18.jar'
        Url = 'https://repo.maven.apache.org/maven2/nz/ac/waikato/cms/weka/thirdparty/bounce/0.18/bounce-0.18.jar'
        SHA256 = 'bffff1505335c02256b7ab2ccffbe4aa4d3ac9fe14c17557809b7c9d99d666ca'
    }
)
foreach ($artifact in $artifacts) {
    $target = Join-Path $toolsPath $artifact.Name
    if (-not (Test-Path -LiteralPath $target)) {
        Invoke-WebRequest -Uri $artifact.Url -OutFile $target
    }
    $actual = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $artifact.SHA256) {
        throw "Checksum mismatch for $target. Review the file before replacing it."
    }
}
Write-Output "WEKA 3.8.6 and Bounce 0.18 verified in $toolsPath"

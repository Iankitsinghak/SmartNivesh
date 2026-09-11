Add-Type -AssemblyName System.Drawing

$width = 1920; $height = 1240
$bitmap = [System.Drawing.Bitmap]::new($width, $height)
$g = [System.Drawing.Graphics]::FromImage($bitmap)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$g.Clear([System.Drawing.Color]::FromArgb(248, 250, 252))

function C([string]$hex) { [System.Drawing.ColorTranslator]::FromHtml($hex) }
function Font([single]$size, [bool]$bold=$false) { [System.Drawing.Font]::new('Segoe UI', $size, $(if($bold){[System.Drawing.FontStyle]::Bold}else{[System.Drawing.FontStyle]::Regular}), [System.Drawing.GraphicsUnit]::Pixel) }
function Text([string]$value, [single]$x, [single]$y, [single]$size, [string]$color, [bool]$bold=$false, [string]$align='center') {
  $format=[System.Drawing.StringFormat]::new(); if($align -eq 'left'){$format.Alignment=[System.Drawing.StringAlignment]::Near}elseif($align -eq 'right'){$format.Alignment=[System.Drawing.StringAlignment]::Far}else{$format.Alignment=[System.Drawing.StringAlignment]::Center}; $format.LineAlignment=[System.Drawing.StringAlignment]::Center
  $g.DrawString($value,(Font $size $bold),[System.Drawing.SolidBrush]::new((C $color)),$x,$y,$format)
}
function RoundRect([single]$x,[single]$y,[single]$w,[single]$h,[single]$r,[string]$fill,[string]$stroke) {
  $p=[System.Drawing.Drawing2D.GraphicsPath]::new(); $d=$r*2
  $p.AddArc($x,$y,$d,$d,180,90); $p.AddArc($x+$w-$d,$y,$d,$d,270,90); $p.AddArc($x+$w-$d,$y+$h-$d,$d,$d,0,90); $p.AddArc($x,$y+$h-$d,$d,$d,90,90); $p.CloseFigure()
  $g.FillPath([System.Drawing.SolidBrush]::new((C $fill)),$p); $g.DrawPath([System.Drawing.Pen]::new((C $stroke),2),$p)
}
function Arrow([single]$x1,[single]$y1,[single]$x2,[single]$y2) {
  $pen=[System.Drawing.Pen]::new((C '#64748B'),4); $pen.CustomEndCap=[System.Drawing.Drawing2D.AdjustableArrowCap]::new(8,9,$true); $g.DrawLine($pen,$x1,$y1,$x2,$y2)
}
function Pill([string]$label,[single]$x,[single]$y,[string]$fill,[string]$ink) { RoundRect $x $y 160 42 21 $fill $fill; Text $label ($x+80) ($y+21) 17 $ink $true }
function Card([single]$x,[single]$y,[single]$w,[single]$h,[string]$accent,[string]$eyebrow,[string]$title,[string[]]$items) {
  RoundRect $x $y $w $h 26 '#FFFFFF' $accent
  $g.FillRectangle([System.Drawing.SolidBrush]::new((C $accent)),$x,$y+1,$w,9)
  Text $eyebrow ($x+28) ($y+35) 15 $accent $true 'left'; Text $title ($x+28) ($y+70) 27 '#0F172A' $true 'left'
  $rowY=$y+118; foreach($item in $items){ $g.FillEllipse([System.Drawing.SolidBrush]::new((C $accent)),$x+30,$rowY-6,12,12); Text $item ($x+54) $rowY 18 '#334155' $false 'left'; $rowY+=34 }
}

# title
Text 'VyaparSathi' 960 66 46 '#0F2D5C' $true
Text 'CURRENT ARCHITECTURE & DECISION FLOW' 960 112 19 '#64748B' $true

# Top capability cards
Card 120 164 500 235 '#2563EB' 'PRESENTATION LAYER' 'Entrepreneur Console' @('React 18', 'TypeScript', 'Vite')
Card 710 164 500 235 '#0F9D80' 'APPLICATION LAYER' 'API and Validation' @('FastAPI', 'Python 3.11+', 'Pydantic')
Card 1300 164 500 235 '#F97316' 'PUBLIC DATA LAYER' 'Evidence Sources' @('OpenStreetMap + Overpass', 'Census of India', 'Official scheme and HCES data')

# connectors
Arrow 370 399 370 470; Arrow 960 399 960 470; Arrow 1550 399 1550 470
Arrow 370 470 960 470; Arrow 1550 470 960 470; Arrow 960 470 960 512

# engine
RoundRect 220 512 1480 278 30 '#FFF9ED' '#F59E0B'
$g.FillRectangle([System.Drawing.SolidBrush]::new((C '#F59E0B')),220,513,1480,10)
Text 'DETERMINISTIC INTELLIGENCE ENGINE' 960 557 31 '#B45309' $true
Text 'Calculate  /  Validate  /  Explain  /  Recommend' 960 591 19 '#92400E' $false
$labels=@(@('01','Location','boundaries and zones'),@('02','Market','POIs and competitors'),@('03','Opportunity','gap and score'),@('04','Finance','rules and sizing'),@('05','Schemes','eligibility routing'),@('06','Risk','readiness checks'))
$start=290; foreach($entry in $labels){ $n=$entry[0];$a=$entry[1];$b=$entry[2]; $g.FillEllipse([System.Drawing.SolidBrush]::new((C '#FFF0CE')),$start,645,64,64); Text $n ($start+32) 677 19 '#D97706' $true; Text $a ($start+32) 731 19 '#1F2937' $true; Text $b ($start+32) 757 14 '#64748B' $false; $start+=230 }

Arrow 960 790 960 850

# output section
RoundRect 350 850 1220 180 30 '#F5F3FF' '#7C3AED'
$g.FillRectangle([System.Drawing.SolidBrush]::new((C '#7C3AED')),350,851,1220,10)
Text 'EXPLAINABLE OUTCOME' 960 892 27 '#5B21B6' $true
Text 'Structured report  |  evidence and limitations  |  recommended next steps' 960 925 18 '#6D28D9' $false
Pill 'Decision report' 485 958 '#EDE9FE' '#5B21B6'; Pill 'AI explanation*' 880 958 '#EDE9FE' '#5B21B6'; Pill 'Action plan' 1275 958 '#EDE9FE' '#5B21B6'

# bottom principles
RoundRect 120 1085 1680 86 24 '#0F2D5C' '#0F2D5C'
Text 'Evidence-led inputs' 370 1128 22 '#FFFFFF' $true; Text '>' 610 1128 26 '#93C5FD' $true
Text 'Deterministic scoring' 840 1128 22 '#FFFFFF' $true; Text '>' 1110 1128 26 '#93C5FD' $true
Text 'Explainable guidance' 1360 1128 22 '#FFFFFF' $true
Text '* LLM provider-agnostic; explanations never replace deterministic scores.' 960 1204 15 '#64748B' $false

$out = Join-Path $PSScriptRoot 'vyaparsathi-architecture-flow.png'
$bitmap.Save($out,[System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bitmap.Dispose()

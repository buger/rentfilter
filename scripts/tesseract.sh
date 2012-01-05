convert -resize 500x40 -negate -threshold 20% -negate -despeckle -monochrome http://1.static.slando.com/captcha/d40e4d1681941bb1c1df181b8169f72a.png numbers1.tif
tesseract numbers1.tif result -l eng

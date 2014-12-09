diff --git a/ckanext/graph/theme/public/vendor/jquery.flot.barnumbers.js b/ckanext/graph/theme/public/vendor/jquery.flot.barnumbers.js
index 0a10ace..0f97487 100644
--- a/ckanext/graph/theme/public/vendor/jquery.flot.barnumbers.js
+++ b/ckanext/graph/theme/public/vendor/jquery.flot.barnumbers.js
@@ -69,7 +69,7 @@
                         text = points[barNumber];
                     }
                     var c = plot.p2c(point);
-                    ctx.fillText(text.toString(10), c.left + offset.left, c.top + offset.top + 3)
+                    ctx.fillText(text.toString(10), c.left + offset.left, c.top + offset.top + series.bars.numbers.top || 3)
                 }
             }
         });

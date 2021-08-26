/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 */

var gulp = require('gulp');
var $ = require('gulp-load-plugins')();
var merge = require('merge-stream');

var paths = {
    jade: 'partials/*.jade',
    coffee: 'coffee/*.coffee',
    images: 'images/**/*',
    dist: 'dist/'
};

gulp.task('copy-config', function() {
    return gulp.src('threefold-auth.json')
        .pipe(gulp.dest(paths.dist));
});

gulp.task('copy-images', function() {
    return gulp.src(paths.images)
        .pipe(gulp.dest(paths.dist + "images"));
});

gulp.task('compile', function() {
    var jade = gulp.src(paths.jade)
        .pipe($.plumber())
        .pipe($.cached('jade'))
        .pipe($.jade({pretty: true}))
        .pipe($.angularTemplatecache({
            transformUrl: function(url) {
                return '/plugins/threefold-auth/' + url;
            }
        }))
        .pipe($.remember('jade'));

    var coffee = gulp.src(paths.coffee)
        .pipe($.plumber())
        .pipe($.cached('coffee'))
        .pipe($.coffee())
        .pipe($.remember('coffee'));

    return merge(jade, coffee)
        .pipe($.concat('threefold-auth.js'))
        .pipe($.uglify({mangle:false, preserveComments: false}))
        .pipe(gulp.dest(paths.dist));
});

gulp.task('watch', function() {
    gulp.watch([paths.jade, paths.coffee, paths.images], ['copy-images', 'compile']);
});

gulp.task('default', ['copy-config', 'copy-images', 'compile', 'watch']);

gulp.task('build', ['copy-config', 'copy-images', 'compile', ]);

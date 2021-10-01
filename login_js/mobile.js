

function r(n, r) {
    var u = i(n);
    EnCryptData = u + r
    return  t(EnCryptData)
}

function n(n) {
    for (var i = "", r = "", u, t = 0; t <= 3; t++) u = n >>> t * 8 & 255, r = "0" + u.toString(16), i = i + r.substr(r.length - 2, 2);
    return i
}

var t = function (t) {
    function v(n, t) {
        return n << t | n >>> 32 - t
    }

    function s(n, t) {
        var f, e, r, u, i;
        return (r = n & 2147483648, u = t & 2147483648, f = n & 1073741824, e = t & 1073741824, i = (n & 1073741823) + (t & 1073741823), f & e) ? i ^ 2147483648 ^ r ^ u : f | e ? i & 1073741824 ? i ^ 3221225472 ^ r ^ u : i ^ 1073741824 ^ r ^ u : i ^ r ^ u
    }

    function yt(n, t, i) {
        return n & t | ~n & i
    }

    function pt(n, t, i) {
        return n & i | t & ~i
    }

    function wt(n, t, i) {
        return n ^ t ^ i
    }

    function bt(n, t, i) {
        return t ^ (n | ~i)
    }

    function h(n, t, i, r, u, f, e) {
        return n = s(n, s(s(yt(t, i, r), u), e)), s(v(n, f), t)
    }

    function c(n, t, i, r, u, f, e) {
        return n = s(n, s(s(pt(t, i, r), u), e)), s(v(n, f), t)
    }

    function l(n, t, i, r, u, f, e) {
        return n = s(n, s(s(wt(t, i, r), u), e)), s(v(n, f), t)
    }

    function a(n, t, i, r, u, f, e) {
        return n = s(n, s(s(bt(t, i, r), u), e)), s(v(n, f), t)
    }

    function kt(n) {
        for (var r, u = n.length, o = u + 8, s = (o - o % 64) / 64, e = (s + 1) * 16, i = Array(e - 1), f = 0, t = 0; t < u;) r = (t - t % 4) / 4, f = t % 4 * 8, i[r] = i[r] | n.charCodeAt(t) << f, t++;
        return r = (t - t % 4) / 4, f = t % 4 * 8, i[r] = i[r] | 128 << f, i[e - 2] = u << 3, i[e - 1] = u >>> 29, i
    }

    function dt(n) {
        var i, r, t;
        for (n = n.replace(/\r\n/g, "\n"), i = "", r = 0; r < n.length; r++) t = n.charCodeAt(r), t < 128 ? i += String.fromCharCode(t) : t > 127 && t < 2048 ? (i += String.fromCharCode(t >> 6 | 192), i += String.fromCharCode(t & 63 | 128)) : (i += String.fromCharCode(t >> 12 | 224), i += String.fromCharCode(t >> 6 & 63 | 128), i += String.fromCharCode(t & 63 | 128));
        return i
    }
    var o = Array(),
        e, ht, ct, lt, at, i, r, u, f, y = 7,
        p = 12,
        w = 17,
        b = 22,
        k = 5,
        d = 9,
        g = 14,
        nt = 20,
        tt = 4,
        it = 11,
        rt = 16,
        ut = 23,
        ft = 6,
        et = 10,
        ot = 15,
        st = 21,
        vt;
    for (t = dt(t), o = kt(t), i = 1732584193, r = 4023233417, u = 2562383102, f = 271733878, e = 0; e < o.length; e += 16) ht = i, ct = r, lt = u, at = f, i = h(i, r, u, f, o[e + 0], y, 3614090360), f = h(f, i, r, u, o[e + 1], p, 3905402710), u = h(u, f, i, r, o[e + 2], w, 606105819), r = h(r, u, f, i, o[e + 3], b, 3250441966), i = h(i, r, u, f, o[e + 4], y, 4118548399), f = h(f, i, r, u, o[e + 5], p, 1200080426), u = h(u, f, i, r, o[e + 6], w, 2821735955), r = h(r, u, f, i, o[e + 7], b, 4249261313), i = h(i, r, u, f, o[e + 8], y, 1770035416), f = h(f, i, r, u, o[e + 9], p, 2336552879), u = h(u, f, i, r, o[e + 10], w, 4294925233), r = h(r, u, f, i, o[e + 11], b, 2304563134), i = h(i, r, u, f, o[e + 12], y, 1804603682), f = h(f, i, r, u, o[e + 13], p, 4254626195), u = h(u, f, i, r, o[e + 14], w, 2792965006), r = h(r, u, f, i, o[e + 15], b, 1236535329), i = c(i, r, u, f, o[e + 1], k, 4129170786), f = c(f, i, r, u, o[e + 6], d, 3225465664), u = c(u, f, i, r, o[e + 11], g, 643717713), r = c(r, u, f, i, o[e + 0], nt, 3921069994), i = c(i, r, u, f, o[e + 5], k, 3593408605), f = c(f, i, r, u, o[e + 10], d, 38016083), u = c(u, f, i, r, o[e + 15], g, 3634488961), r = c(r, u, f, i, o[e + 4], nt, 3889429448), i = c(i, r, u, f, o[e + 9], k, 568446438), f = c(f, i, r, u, o[e + 14], d, 3275163606), u = c(u, f, i, r, o[e + 3], g, 4107603335), r = c(r, u, f, i, o[e + 8], nt, 1163531501), i = c(i, r, u, f, o[e + 13], k, 2850285829), f = c(f, i, r, u, o[e + 2], d, 4243563512), u = c(u, f, i, r, o[e + 7], g, 1735328473), r = c(r, u, f, i, o[e + 12], nt, 2368359562), i = l(i, r, u, f, o[e + 5], tt, 4294588738), f = l(f, i, r, u, o[e + 8], it, 2272392833), u = l(u, f, i, r, o[e + 11], rt, 1839030562), r = l(r, u, f, i, o[e + 14], ut, 4259657740), i = l(i, r, u, f, o[e + 1], tt, 2763975236), f = l(f, i, r, u, o[e + 4], it, 1272893353), u = l(u, f, i, r, o[e + 7], rt, 4139469664), r = l(r, u, f, i, o[e + 10], ut, 3200236656), i = l(i, r, u, f, o[e + 13], tt, 681279174), f = l(f, i, r, u, o[e + 0], it, 3936430074), u = l(u, f, i, r, o[e + 3], rt, 3572445317), r = l(r, u, f, i, o[e + 6], ut, 76029189), i = l(i, r, u, f, o[e + 9], tt, 3654602809), f = l(f, i, r, u, o[e + 12], it, 3873151461), u = l(u, f, i, r, o[e + 15], rt, 530742520), r = l(r, u, f, i, o[e + 2], ut, 3299628645), i = a(i, r, u, f, o[e + 0], ft, 4096336452), f = a(f, i, r, u, o[e + 7], et, 1126891415), u = a(u, f, i, r, o[e + 14], ot, 2878612391), r = a(r, u, f, i, o[e + 5], st, 4237533241), i = a(i, r, u, f, o[e + 12], ft, 1700485571), f = a(f, i, r, u, o[e + 3], et, 2399980690), u = a(u, f, i, r, o[e + 10], ot, 4293915773), r = a(r, u, f, i, o[e + 1], st, 2240044497), i = a(i, r, u, f, o[e + 8], ft, 1873313359), f = a(f, i, r, u, o[e + 15], et, 4264355552), u = a(u, f, i, r, o[e + 6], ot, 2734768916), r = a(r, u, f, i, o[e + 13], st, 1309151649), i = a(i, r, u, f, o[e + 4], ft, 4149444226), f = a(f, i, r, u, o[e + 11], et, 3174756917), u = a(u, f, i, r, o[e + 2], ot, 718787259), r = a(r, u, f, i, o[e + 9], st, 3951481745), i = s(i, ht), r = s(r, ct), u = s(u, lt), f = s(f, at);
    return vt = n(i) + n(r) + n(u) + n(f), vt.toLowerCase()
},
    i = function (n) {
        function l(n) {
            for (var r, i = "", t = 1; t <= n.length; t++) i += n.charAt(t - 1).charCodeAt(0);
            return r = new Number(i), r.toString(16)
        }
        var e = 30,
            o, h, s, u, i, c, r, f, t;
        if (o = e - n.length, o > 1)
            for (s = 1; s <= o; s++) n = n + String.fromCharCode(21);
        for (u = new Number(1), i = 1; i <= e; i++) h = e + n.charAt(i - 1).charCodeAt(0) * i, u = u * h;
        for (c = new Number(u.toPrecision(15)), n = c.toString().toUpperCase(), r = "", t = 1; t <= n.length; t++) r = r + l(n.substring(t - 1, t + 2));
        for (f = "", t = 20; t <= r.length - 18; t += 2) f = f + r.charAt(t - 1);
        return f.toUpperCase()
    };


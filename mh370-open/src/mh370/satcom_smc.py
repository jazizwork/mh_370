"""Adaptive-tempering Sequential Monte Carlo sampler (workstream A).

Standard SMC sampler (Del Moral, Doucet & Jasra 2006; adaptive tempering as in Jasra et al.
2011): particles from the prior are moved through targets pi_b ~ prior * L^b, b: 0 -> 1, with
b chosen so that the effective sample size drops to `ess_frac`*N at each stage, systematic
resampling, then random-walk Metropolis moves with a proposal covariance estimated from the
particle cloud.  The log marginal likelihood (evidence) is accumulated from the incremental
weights and is used to weight the autopilot modes against each other.
"""
from __future__ import annotations

import numpy as np


class BoxGaussPrior:
    """Independent priors: Gaussian ('g', mean, sd) or uniform ('u', lo, hi) per dimension."""

    def __init__(self, spec):
        self.spec = spec
        self.d = len(spec)

    def sample(self, n, rng):
        x = np.empty((n, self.d))
        for j, (kind, a, b) in enumerate(self.spec):
            x[:, j] = rng.normal(a, b, n) if kind == "g" else rng.uniform(a, b, n)
        return x

    def logpdf(self, x):
        lp = np.zeros(x.shape[0])
        for j, (kind, a, b) in enumerate(self.spec):
            if kind == "g":
                lp += -0.5 * ((x[:, j] - a) / b) ** 2 - np.log(b * np.sqrt(2 * np.pi))
            else:
                inside = (x[:, j] >= a) & (x[:, j] <= b)
                lp += np.where(inside, -np.log(b - a), -np.inf)
        return lp


def _systematic(w, rng):
    n = w.size
    u = (rng.random() + np.arange(n)) / n
    c = np.cumsum(w)
    c[-1] = 1.0
    return np.searchsorted(c, u)


def smc(loglik, prior, n=10000, seed=0, ess_frac=0.5, min_moves=4, max_moves=25,
        target_moves=2.0, verbose=True, log=print):
    rng = np.random.default_rng(seed)
    x = prior.sample(n, rng)
    lp = prior.logpdf(x)
    ll = _safe(loglik(x))
    beta, logz, stage = 0.0, 0.0, 0
    scale = 0.5
    hist = []
    while beta < 1.0:
        stage += 1

        def ess(b):
            lw = (b - beta) * ll
            lw = lw - lw.max()
            w = np.exp(lw)
            return w.sum() ** 2 / np.sum(w ** 2)

        if ess(1.0) >= ess_frac * n:
            bnew = 1.0
        else:
            lo, hi = beta, 1.0
            for _ in range(60):
                mid = 0.5 * (lo + hi)
                if ess(mid) < ess_frac * n:
                    hi = mid
                else:
                    lo = mid
            bnew = max(lo, beta + 1e-12)
        lw = (bnew - beta) * ll
        m = lw.max()
        w = np.exp(lw - m)
        logz += m + np.log(w.mean())
        w /= w.sum()
        idx = _systematic(w, rng)
        x, ll, lp = x[idx], ll[idx], lp[idx]
        beta = bnew
        # --- Metropolis moves -------------------------------------------------------
        cov = np.cov(x.T) + np.diag(1e-12 + 1e-8 * np.var(x, 0))
        L = np.linalg.cholesky(cov)
        moved = 0.0
        nuniq0 = np.unique(x[:, 0]).size
        for k in range(max_moves):
            prop = x + scale * (2.38 / np.sqrt(prior.d)) * (rng.standard_normal(x.shape) @ L.T)
            lpp = prior.logpdf(prop)
            ok = np.isfinite(lpp)
            llp = np.full(n, -np.inf)
            if ok.any():
                llp[ok] = _safe(loglik(prop[ok]))
            loga = beta * (llp - ll) + lpp - lp
            acc = np.log(rng.random(n)) < loga
            x[acc], ll[acc], lp[acc] = prop[acc], llp[acc], lpp[acc]
            rate = acc.mean()
            moved += rate
            scale *= np.exp(0.6 * (rate - 0.25))
            scale = float(np.clip(scale, 0.02, 3.0))
            if k + 1 >= min_moves and moved >= target_moves:
                break
        hist.append(dict(stage=stage, beta=beta, logz=logz, moves=k + 1, acc=moved / (k + 1),
                         scale=scale, unique_before=nuniq0, ll_max=float(ll.max()),
                         ll_med=float(np.median(ll))))
        if verbose:
            log(f"stage {stage:3d} beta={beta:.3e} logZ={logz:10.2f} moves={k+1:2d} "
                f"acc={moved/(k+1):.2f} scale={scale:.2f} uniq={nuniq0} llmax={ll.max():.1f} "
                f"llmed={np.median(ll):.1f}")
    return dict(x=x, ll=ll, lp=lp, logz=logz, hist=hist)


def _safe(v):
    v = np.asarray(v, float)
    return np.where(np.isfinite(v), v, -np.inf)

MVSKT = function(X50,w0){

  library(highOrderPortfolios)
  X_moments <- estimate_moments(X50, adjust_magnitude = TRUE)
  
  #w0 <- rep(1/50, 50)
  w0_moments <- eval_portfolio_moments(w0, X_moments)
  d <- abs(w0_moments)
  kappa <- 0.3 * sqrt(w0 %*% X_moments$Sgm %*% w0)
  # portfolio optimization
  sol <- design_MVSKtilting_portfolio(d, X_moments, w_init = w0, w0 = w0,
                                      w0_moments = w0_moments, kappa = kappa,
                                      ftol = 1e-10)
  sol
}


MVSK = function(X50){
  
  library(highOrderPortfolios)
  X_moments <- estimate_moments(X50)
  xi <- 10
  lmd <- c(1, xi/2, xi*(xi+1)/6, xi*(xi+1)*(xi+2)/24)
  # portfolio optimization
  sol <- design_MVSK_portfolio(lmd, X_moments)
  sol
}

myadd = function(x1,x2){
  x3 = x1 + x2
  x3
}


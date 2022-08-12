
from cgi import test
import string
from sklearn import svm, metrics
from sklearn.model_selection import cross_val_score, KFold, train_test_split


class Results:
    def __init__(self):
        self.demo_deg = None

tsa_res = Results()


class MLmodel:
    def __init__(self, model: string, params: dict, X, y ,  test_ratio = 0.25, random_seed = 10, kfoldnum = 5) -> None:
        self.model = model
        self.X = X
        self.y = y
        self.params = params
        self.test_ratio = test_ratio
        self.res = None
        self.seed = random_seed
        self.kfold_num = kfoldnum

    def svm_clf(self) -> None:
        clf = svm.SVC(
            kernel  = self.params['kernel'], 
            C       = self.params['C'],
            degree  = self.params['degree']
        )
        X_train, X_test, y_train, y_test = train_test_split(self.X, self.y, test_size=self.test_ratio, random_state=self.seed)
        clf.fit(X_train, y_train)
        y_train_pred = clf.predict(X_train)
        y_test_pred = clf.predict(X_test)
        kfold = KFold(self.kfold_num)
        self.res = {
            'model' : self.model,
            'fbeta': metrics.fbeta_score(y_test, y_test_pred, beta = 0.5),
            'f1_score': metrics.f1_score(y_test, y_test_pred), 
            'accuracy_train': metrics.accuracy_score(y_train, y_train_pred),
            'cross_val': cross_val_score(clf, self.X, self.y, cv = kfold).mean()
        }

    def fit(self):
        if self.model == 'Support-Vector-Machine':
            return self.svm_clf()
